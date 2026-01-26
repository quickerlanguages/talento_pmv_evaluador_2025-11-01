# backend/talento_backend_v2/lib/ccp_answer_helpers.py
from __future__ import annotations
import time
import json
from typing import Any

from django.conf import settings
from django.db import IntegrityError, connection
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime as dt_parse

# Ajusta estos imports a tu árbol real (según lo que vi en tu screenshot)
from talento_backend_v2.lib.http_responses import json_bad_request
from talento_backend_v2.lib.metrics import _metric_inc
 # NOTE: normalize_mode may not exist in some evaluator bundles. Keep a local fallback.
try:
    from talento_backend_v2.lib.dates import normalize_mode  # type: ignore
except Exception:  # pragma: no cover
    def normalize_mode(v: Any, default: str = "training") -> str:
        """Normalize mode strings.

        Accepted aliases:
          - training: train, t
          - assessment: eval, evaluation, assess, assessment, a, e
          - all: all
        """
        s = (str(v).strip().lower() if v is not None else "")
        if not s:
            return default
        if s in ("training", "train", "t"):
            return "training"
        if s in ("assessment", "assess", "eval", "evaluation", "e", "a"):
            return "assessment"
        if s == "all":
            return "all"
        return default
from talento_backend_v2.lib.schema_cache import _table_exists, _table_has_column

# Si el scoring puro vive en talento_domain, importa aquí:
# from talento_domain.ccp.scoring import compute_correcta_from_truth_any


# ------------------------------------------------------------
# Globals
# ------------------------------------------------------------
_TLT_RESPUESTA_UNIQUE_INDEXES_ENSURED = False


# ------------------------------------------------------------
# Small utilities (self-contained; no view imports)
# ------------------------------------------------------------
def _to_bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        try:
            return bool(int(v))
        except Exception:
            return default
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "t", "yes", "y", "si", "sí"):
            return True
        if s in ("0", "false", "f", "no", "n"):
            return False
    return default


def normalize_correcta_out(v: Any):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    try:
        return bool(int(v))
    except Exception:
        return None


def _resolve_user_answer_from_payload(data: dict, meta: dict):
    # Canonical + legacy aliases
    for k in ("user_answer", "answer", "response"):
        if k in data:
            return data.get(k)
    if isinstance(meta, dict):
        for k in ("user_answer", "answer", "response"):
            if k in meta:
                return meta.get(k)
    return None


# ------------------------------------------------------------
# Answer normalization and correctness helpers
# ------------------------------------------------------------

def _normalize_answer_token(v: Any) -> str | None:
    """Normalize user answers and truth values into a comparable token.

    This is intentionally permissive to support evaluator bundles with slightly
    different front-end encodings.
    """
    if v is None:
        return None

    # Unwrap simple containers
    if isinstance(v, (list, tuple)) and len(v) == 1:
        v = v[0]

    # bool/int
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)

    # strings
    if isinstance(v, str):
        s = v.strip()
        if s == "":
            return None
        sl = s.lower()

        # yes/no style
        if sl in ("1", "true", "t", "yes", "y", "si", "sí"):
            return "1"
        if sl in ("0", "false", "f", "no", "n"):
            return "0"

        # same/diff style
        if sl in ("same", "igual", "iguales", "s", "="):
            return "same"
        if sl in ("diff", "different", "d", "distinto", "diferente", "noigual", "!=", "≠"):
            return "diff"

        # common check/cross icons
        if s in ("✓", "✔", "✅", "☑"):
            return "1"
        if s in ("✗", "✘", "❌"):
            return "0"

        # keep numbers as-is
        if sl.isdigit():
            return sl

        return sl

    # dicts: try to extract a primitive
    if isinstance(v, dict):
        for k in (
            "truth",
            "expected",
            "answer",
            "correct_answer",
            "correct",
            "correcta",
            "value",
            "response",
        ):
            if k in v:
                return _normalize_answer_token(v.get(k))

    return None


def _extract_truth_token(truth: Any) -> str | None:
    """Extract the comparable token from a truth payload."""
    if truth is None:
        return None

    # If truth is JSON string, try parsing
    if isinstance(truth, str):
        ts = truth.strip()
        if ts.startswith("{") or ts.startswith("["):
            try:
                parsed = json.loads(ts)
                return _extract_truth_token(parsed)
            except Exception:
                return _normalize_answer_token(ts)
        return _normalize_answer_token(ts)

    # dict/list
    if isinstance(truth, dict):
        # Prefer explicit expected/correct answer fields
        for k in ("correct_answer", "expected", "answer", "truth", "response", "value"):
            if k in truth:
                return _normalize_answer_token(truth.get(k))
        # Sometimes stored as {"same": true} / {"diff": true}
        for k in ("same", "diff"):
            if k in truth and isinstance(truth.get(k), bool):
                return k if truth.get(k) else ("diff" if k == "same" else "same")
        return _normalize_answer_token(truth)

    if isinstance(truth, (list, tuple)):
        # If a list of acceptable answers is provided
        if len(truth) == 0:
            return None
        # If a single-element list
        if len(truth) == 1:
            return _extract_truth_token(truth[0])
        # Multiple acceptable values: we'll represent as None and handle separately
        return None

    return _normalize_answer_token(truth)


def _compute_correcta_from_truth(ccp_code: Any, sub_code: Any, truth: Any, user_answer: Any):
    """Compute correctness and optional correction flags.

    Returns (is_correct_int|None, correction_flags: dict).

    This function is designed to be tolerant to schema drift between bundles.
    """
    correction_flags: dict[str, Any] = {}

    # Normalize inputs
    u_tok = _normalize_answer_token(user_answer)

    # Handle multi-acceptable truth list
    if isinstance(truth, (list, tuple)) and len(truth) > 1:
        acceptable = {_normalize_answer_token(x) for x in truth}
        acceptable.discard(None)
        if u_tok is None:
            return (None, correction_flags)
        is_ok = 1 if u_tok in acceptable else 0
        return (is_ok, correction_flags)

    t_tok = _extract_truth_token(truth)

    # If either is missing, cannot compute
    if u_tok is None or t_tok is None:
        return (None, correction_flags)

    # Autocorrect a few legacy encodings for VPM icon tasks
    sub_u = (str(sub_code).strip().upper() if sub_code is not None else "")
    if sub_u.endswith("ICON") or "ICON" in sub_u:
        # Some UIs send 'same'/'diff' as 1/0 or vice-versa.
        # If truth is same/diff but user is 1/0, map deterministically.
        if t_tok in ("same", "diff") and u_tok in ("1", "0"):
            mapped = "same" if u_tok == "1" else "diff"
            correction_flags["autocorrect"] = {"from": u_tok, "to": mapped, "reason": "icon_boolean_to_same_diff"}
            u_tok = mapped
        elif t_tok in ("1", "0") and u_tok in ("same", "diff"):
            mapped = "1" if u_tok == "same" else "0"
            correction_flags["autocorrect"] = {"from": u_tok, "to": mapped, "reason": "same_diff_to_icon_boolean"}
            u_tok = mapped

    is_correct_int = 1 if u_tok == t_tok else 0
    return (is_correct_int, correction_flags)


def _build_answer_payload(
    *,
    sesion_id: int,
    trial_id: str,
    item_id: Any,
    ccp_code: Any,
    sub_code: Any,
    mode: Any,
    correcta: Any,
    idempotency_key: Any,
    deduped: bool,
    warning: str | None,
    flags: Any,
) -> dict[str, Any]:
    return {
        "ok": True,
        "sesion_id": int(sesion_id),
        "trial_id": str(trial_id),
        "item_id": item_id,
        "ccp_code": (ccp_code or "").strip().upper() if isinstance(ccp_code, str) else ccp_code,
        "sub_code": (sub_code or "").strip().upper() if isinstance(sub_code, str) else sub_code,
        "mode": mode,
        "correcta": normalize_correcta_out(correcta),
        "idempotency_key": idempotency_key,
        "deduped": bool(deduped),
        "warning": warning,
        "flags": flags or {},
    }


# ------------------------------------------------------------
# Audit (best-effort, never breaks tests)
# ------------------------------------------------------------
def _audit_event_insert(*, sesion_id: int, trial_id: str, event_type: str, severity: str, meta: dict):
    """
    Best-effort audit sink. If you already have a proper audit table/helper elsewhere,
    you can replace this body to call it. For now: never raise.
    """
    try:
        if not _table_exists("tlt_audit_event"):
            return
        has_meta = _table_has_column("tlt_audit_event", "meta_json")
        has_created_at = _table_has_column("tlt_audit_event", "created_at")
        cols = ["sesion_id", "trial_id", "event_type", "severity"]
        vals = ["%s", "%s", "%s", "%s"]
        params = [int(sesion_id), str(trial_id), str(event_type), str(severity)]
        if has_meta:
            cols.append("meta_json")
            vals.append("%s")
            params.append(json.dumps(meta or {}, ensure_ascii=False))
        if has_created_at:
            cols.append("created_at")
            vals.append("CURRENT_TIMESTAMP")

        sql = f"INSERT INTO tlt_audit_event ({', '.join(cols)}) VALUES ({', '.join(vals)})"
        with connection.cursor() as cur:
            cur.execute(sql, params)
    except Exception:
        return


# ------------------------------------------------------------
# Unique indexes (idempotency)
# ------------------------------------------------------------
def _ensure_tlt_respuesta_unique_indexes_best_effort() -> None:
    global _TLT_RESPUESTA_UNIQUE_INDEXES_ENSURED
    if _TLT_RESPUESTA_UNIQUE_INDEXES_ENSURED:
        return

    try:
        if not _table_exists("tlt_respuesta"):
            return
    except Exception:
        return

    try:
        with connection.cursor() as cur:
            cols: set[str] = set()
            try:
                if getattr(connection, "vendor", None) == "sqlite":
                    cur.execute("PRAGMA table_info('tlt_respuesta')")
                    cols = {row[1] for row in cur.fetchall() if row and len(row) > 1}
            except Exception:
                cols = set()

            if (not cols) or {"sesion_id", "trial_id"}.issubset(cols):
                try:
                    cur.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tlt_respuesta__sesion_trial__uniq "
                        "ON tlt_respuesta (sesion_id, trial_id)"
                    )
                except Exception:
                    pass

            if (not cols) or {"sesion_id", "idempotency_key"}.issubset(cols):
                try:
                    cur.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tlt_respuesta__sesion_idem__uniq "
                        "ON tlt_respuesta (sesion_id, idempotency_key)"
                    )
                except Exception:
                    pass

        _TLT_RESPUESTA_UNIQUE_INDEXES_ENSURED = True
    except Exception:
        return


def _ensure_dedupe_index_once():
    # Backwards-compatible alias to your preferred name
    return _ensure_tlt_respuesta_unique_indexes_best_effort()


# ------------------------------------------------------------
# Parse request
# ------------------------------------------------------------
def _parse_answer_request(request):
    """Parsea JSON + normaliza campos base de api_ccp_play_answer.

    Devuelve (error_response, ctx_dict).
    """
    _ensure_dedupe_index_once()

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return (json_bad_request("JSON inválido"), {})

    if not isinstance(data, dict):
        return (json_bad_request("JSON inválido (objeto requerido)"), {})

    _metric_inc("answer_total", 1)

    meta = data.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}

    trial_id = data.get("trial_id") or meta.get("trial_id")
    if isinstance(trial_id, str):
        trial_id = trial_id.strip() or None

    item_id = data.get("item_id") or meta.get("item_id")
    if isinstance(item_id, str):
        item_id = item_id.strip() or None

    idem = (
        request.META.get("HTTP_X_IDEMPOTENCY_KEY")
        or request.headers.get("X-Idempotency-Key")
        or request.headers.get("X_IDEMPOTENCY_KEY")
    )
    if not idem:
        idem = data.get("idem") or data.get("idempotency_key") or meta.get("idem")

    if isinstance(idem, str):
        idem = idem.strip() or None
    else:
        idem = None

    sesion_id = data.get("sesion_id")
    if not trial_id:
        return (json_bad_request("trial_id requerido (modo riguroso)"), {})

    ccp_code = (data.get("ccp_code") or "VPM").strip().upper()
    sub_code = (data.get("sub_code") or data.get("sub") or "VPM_VIS_ICON").strip().upper()

    mode = normalize_mode(data.get("mode"), default="training")
    if mode == "all":
        mode = "training"

    event_type = data.get("event_type", None)
    if event_type is None:
        event_type = meta.get("event_type", None)
    event_type = (str(event_type).strip() if event_type is not None else None) or None

    correcta = data.get("correcta")
    tr_ms = data.get("tr_ms")

    user_answer = _resolve_user_answer_from_payload(data, meta)

    if sesion_id is None:
        return (json_bad_request("sesion_id requerido"), {})
    try:
        sesion_id = int(sesion_id)
    except Exception:
        return (json_bad_request("sesion_id debe ser entero"), {})
    if sesion_id == 0:
        return (json_bad_request("sesion_id no puede ser 0"), {})

    flags: list[str] = []
    if (user_answer is None) and (tr_ms is not None):
        flags.append("timeout_with_tr_ms")
    if (user_answer is not None) and (tr_ms is None):
        flags.append("answer_without_tr_ms")

    return (
        None,
        {
            "data": data,
            "meta": meta,
            "trial_id": trial_id,
            "item_id": item_id,
            "idempotency_key": idem,
            "sesion_id": sesion_id,
            "ccp_code": ccp_code,
            "sub_code": sub_code,
            "mode": mode,
            "event_type": event_type,
            "user_answer": user_answer,
            "correcta": correcta,
            "tr_ms": tr_ms,
            "flags": flags,
            "forced_timeout_flag": False,
            "forced_timeout_reason": None,
        },
    )


# ------------------------------------------------------------
# Trial load
# ------------------------------------------------------------
def _load_trial_or_400(trial_id: str):
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT
                    sesion_id,
                    ccp_code,
                    ejer_code,
                    item_id,
                    truth_json,
                    stimulus_json,
                    timing_json,
                    served_at,
                    mode
                FROM tlt_trial
                WHERE trial_id = %s
                """,
                [trial_id],
            )
            row = cur.fetchone()
    except Exception:
        row = None

    if not row:
        return json_bad_request("trial_id desconocido (no existe en tlt_trial)")

    return {
        "trial_id": str(trial_id),
        "sesion_id": row[0],
        "ccp_code": row[1],
        "ejer_code": row[2],
        "item_id": row[3],
        "truth_json": row[4],
        "stimulus_json": row[5],
        "timing_json": row[6],
        "served_at": row[7],
        "mode": row[8],
    }


# ------------------------------------------------------------
# Timing context
# ------------------------------------------------------------
def _compute_timing_context(trial: dict):
    timing_cfg = {}
    try:
        timing_cfg = json.loads((trial or {}).get("timing_json") or "{}")
        if not isinstance(timing_cfg, dict):
            timing_cfg = {}
    except Exception:
        timing_cfg = {}

    hard_limit_ms = None
    try:
        hard_limit_ms = int(timing_cfg.get("hard_limit_ms"))
    except Exception:
        hard_limit_ms = None

    served_dt = (trial or {}).get("served_at")
    if isinstance(served_dt, str):
        served_dt = dt_parse(served_dt)

    elapsed_ms = None
    if served_dt is not None:
        try:
            from django.utils import timezone as dj_timezone
            from datetime import timezone as dt_timezone

            now_utc = dj_timezone.now().astimezone(dt_timezone.utc)
            if getattr(served_dt, "tzinfo", None) is None:
                served_utc = served_dt.replace(tzinfo=dt_timezone.utc)
            else:
                served_utc = served_dt.astimezone(dt_timezone.utc)

            elapsed_ms = int((now_utc - served_utc).total_seconds() * 1000)
        except Exception:
            elapsed_ms = None

    TRIAL_EXPIRE_MS = int(getattr(settings, "PANEL_TRIAL_EXPIRE_MS", 5 * 60 * 1000))
    grace_ms = int(getattr(settings, "PANEL_TRIAL_GRACE_MS", 250))

    trial_mode = normalize_mode((trial or {}).get("mode"), default="training")
    if trial_mode == "all":
        trial_mode = "training"

    mode_to_store = trial_mode
    return (hard_limit_ms, elapsed_ms, trial_mode, mode_to_store, grace_ms, TRIAL_EXPIRE_MS)


# ------------------------------------------------------------
# Time policy
# ------------------------------------------------------------
def _apply_time_policy(
    *,
    trial_mode: str,
    hard_limit_ms: int | None,
    elapsed_ms: int | None,
    tr_ms: int | None,
    user_answer,
    grace_ms: int,
    trial_expire_ms: int,
    event_type: str | None,
    flags: list[str],
    forced_timeout_flag: bool,
    forced_timeout_reason: str | None,
):
    def _mark_late_local(flag: str):
        nonlocal event_type
        et = (str(event_type).strip().lower() if event_type is not None else "")
        if not et or et in ("submit", "answer", "answered"):
            event_type = "late"
        if flag and flag not in flags:
            flags.append(flag)

    def _force_timeout_local(flag: str):
        nonlocal forced_timeout_flag, forced_timeout_reason
        forced_timeout_flag = True
        forced_timeout_reason = str(flag or "forced_timeout")
        if flag and flag not in flags:
            flags.append(flag)

    late_marked_local = False

    if trial_mode == "assessment" and hard_limit_ms is not None and elapsed_ms is None:
        _force_timeout_local("assessment_missing_elapsed_forced_timeout")
        user_answer = None
        tr_ms = None

    if elapsed_ms is not None and elapsed_ms > int(trial_expire_ms):
        if trial_mode == "assessment":
            if user_answer is not None:
                _force_timeout_local("trial_expired_forced_timeout")
                user_answer = None
                tr_ms = None
        else:
            if user_answer is not None:
                late_marked_local = True
                _mark_late_local("trial_expired_training")

    if hard_limit_ms is not None and elapsed_ms is not None and elapsed_ms > (int(hard_limit_ms) + int(grace_ms)):
        if trial_mode == "assessment":
            if user_answer is not None:
                _force_timeout_local("late_answer_forced_timeout")
                user_answer = None
                tr_ms = None
        else:
            if user_answer is not None:
                late_marked_local = True
                _mark_late_local("late_answer_training")

    if hard_limit_ms is not None and tr_ms is not None and tr_ms > int(hard_limit_ms):
        if trial_mode == "assessment":
            late_marked_local = True
            _mark_late_local("late_tr_ms_over_hard_limit")
            _force_timeout_local("tr_ms_over_hard_limit_forced_timeout")
            user_answer = None
            tr_ms = None
        else:
            late_marked_local = True
            _mark_late_local("tr_ms_over_hard_limit")

    if bool(forced_timeout_flag) or (user_answer is None):
        tr_ms = None

    return (
        forced_timeout_flag,
        forced_timeout_reason,
        late_marked_local,
        event_type,
        tr_ms,
        user_answer,
        flags,
    )


# ------------------------------------------------------------
# Finalize answer shape
# ------------------------------------------------------------
def _finalize_answer_shape(
    *,
    data: dict,
    user_answer,
    tr_ms,
    is_timeout: bool,
    late_marked: bool,
    trial_mode: str,
    forced_timeout_flag: bool,
    forced_timeout_reason: str | None,
):
    if is_timeout:
        user_answer = None
        tr_ms = None

    if late_marked:
        tr_ms = None
        if (trial_mode or "").strip().lower() == "assessment":
            user_answer = None
            forced_timeout_flag = True
            forced_timeout_reason = forced_timeout_reason or "late_marked_assessment"
            is_timeout = True

    is_blank_val = None
    try:
        if "is_blank" in data:
            is_blank_val = _to_bool(data.get("is_blank"), default=False)
        else:
            if user_answer is None:
                is_blank_val = True
            elif isinstance(user_answer, str) and user_answer.strip() == "":
                is_blank_val = True
            else:
                is_blank_val = False
    except Exception:
        is_blank_val = None

    if is_blank_val:
        user_answer = None
        tr_ms = None

    return (user_answer, tr_ms, is_timeout, is_blank_val, forced_timeout_flag, forced_timeout_reason)


# ------------------------------------------------------------
# Cross-session replay guard
# ------------------------------------------------------------
def _enforce_trial_session_match_or_409(
    sesion_id: int,
    trial: dict,
    *,
    payload_ccp: str | None = None,
    payload_sub: str | None = None,
    idempotency_key: str | None = None,
):
    trial_sesion_id = None
    try:
        trial_sesion_id = trial.get("sesion_id")
        trial_sesion_id = int(trial_sesion_id) if trial_sesion_id is not None else None
    except Exception:
        trial_sesion_id = None

    if trial_sesion_id is not None and int(sesion_id) != int(trial_sesion_id):
        _metric_inc("answer_trial_session_mismatch", 1)
        _metric_inc("answer_conflict", 1)

        _audit_event_insert(
            sesion_id=int(sesion_id),
            trial_id=str(trial.get("trial_id") or ""),
            event_type="cross_session_replay",
            severity="warn",
            meta={
                "payload_sesion_id": int(sesion_id),
                "trial_sesion_id": int(trial_sesion_id),
                "ccp_payload": (payload_ccp or ""),
                "sub_payload": (payload_sub or ""),
                "ccp_trial": (trial.get("ccp_code") or "").strip().upper(),
                "sub_trial": (trial.get("ejer_code") or "").strip().upper(),
                "idempotency_key": idempotency_key,
                "item_id": trial.get("item_id"),
            },
        )

        return JsonResponse(
            {
                "ok": False,
                "error": "trial_id pertenece a otra sesion_id",
                "expected": {"sesion_id": int(trial_sesion_id)},
                "got": {"sesion_id": int(sesion_id)},
            },
            status=409,
        )
    return None


# ------------------------------------------------------------
# Dedupe (IMPORTANT: accept idem / idempotency_key)
# ------------------------------------------------------------
def _try_answer_dedupe_by_mode(*args, **kwargs):
    """
    Devuelve JsonResponse si encuentra respuesta previa, si no None.
    Acepta kwargs:
      - sesion_id
      - trial_id
      - idempotency_key OR idem
    """
    try:
        sesion_id = kwargs.get("sesion_id") if "sesion_id" in kwargs else (args[0] if len(args) >= 1 else None)
        trial_id = kwargs.get("trial_id") if "trial_id" in kwargs else (args[1] if len(args) >= 2 else None)

        # accept both kw names: idempotency_key / idem
        idempotency_key = kwargs.get("idempotency_key")
        if idempotency_key is None:
            idempotency_key = kwargs.get("idem")
        if idempotency_key is None and len(args) >= 3:
            idempotency_key = args[2]

        if sesion_id is None or trial_id is None:
            return None

        try:
            sid_i = int(sesion_id)
        except Exception:
            return None

        tid_s = str(trial_id).strip()
        if not tid_s:
            return None

        idem = None
        if isinstance(idempotency_key, str) and idempotency_key.strip():
            idem = idempotency_key.strip()

        if not _table_exists("tlt_respuesta"):
            return None

        has_created_at = _table_has_column("tlt_respuesta", "created_at")
        has_idem_col = _table_has_column("tlt_respuesta", "idempotency_key")
        has_item_id = _table_has_column("tlt_respuesta", "item_id")
        has_ccp_code = _table_has_column("tlt_respuesta", "ccp_code")
        has_ejer_code = _table_has_column("tlt_respuesta", "ejer_code")
        has_mode = _table_has_column("tlt_respuesta", "mode")
        has_correcta = _table_has_column("tlt_respuesta", "correcta")

        if has_created_at:
            order_clause = " ORDER BY created_at DESC"
        else:
            order_clause = " ORDER BY rowid DESC" if getattr(connection, "vendor", None) == "sqlite" else ""

        item_id_select = "item_id" if has_item_id else "NULL AS item_id"
        ccp_select = "ccp_code" if has_ccp_code else "NULL AS ccp_code"
        sub_select = "ejer_code" if has_ejer_code else "NULL AS ejer_code"
        mode_select = "mode" if has_mode else "NULL AS mode"
        correcta_select = "correcta" if has_correcta else "NULL AS correcta"
        idem_select = "idempotency_key" if has_idem_col else "NULL AS idempotency_key"

        select_list = (
            "sesion_id, trial_id, "
            + item_id_select
            + ", "
            + ccp_select
            + ", "
            + sub_select
            + ", "
            + mode_select
            + ", "
            + correcta_select
            + ", "
            + idem_select
        )

        if idem and has_idem_col:
            sql = (
                "SELECT " + select_list +
                " FROM tlt_respuesta WHERE sesion_id = %s AND idempotency_key = %s" +
                order_clause + " LIMIT 1"
            )
            params = [sid_i, idem]
            dedupe_by = "idempotency_key"
        else:
            sql = (
                "SELECT " + select_list +
                " FROM tlt_respuesta WHERE sesion_id = %s AND trial_id = %s" +
                order_clause + " LIMIT 1"
            )
            params = [sid_i, tid_s]
            dedupe_by = "trial_id"

        with connection.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()

        if not row:
            return None

        stored_sid, stored_tid, item_id, ccp_code, sub_code, mode, correcta, stored_idem = row

        # Best-effort: if respuesta row lacks item_id, try fetching it from tlt_trial
        if item_id in (None, "") and _table_exists("tlt_trial") and _table_has_column("tlt_trial", "item_id"):
            try:
                tid_lookup = str(stored_tid or tid_s)
                with connection.cursor() as cur2:
                    cur2.execute(
                        "SELECT item_id FROM tlt_trial WHERE trial_id = %s LIMIT 1",
                        [tid_lookup],
                    )
                    r2 = cur2.fetchone()
                if r2 and r2[0] not in (None, ""):
                    item_id = r2[0]
            except Exception:
                pass

        payload = _build_answer_payload(
            sesion_id=int(stored_sid) if stored_sid is not None else sid_i,
            trial_id=str(stored_tid or tid_s),
            item_id=item_id,
            ccp_code=ccp_code,
            sub_code=sub_code,
            mode=mode,
            correcta=correcta,
            idempotency_key=(stored_idem if stored_idem not in (None, "") else idem),
            deduped=True,
            warning="deduped",
            flags={"deduped_by": dedupe_by},
        )
        return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})

    except Exception:
        return None


# ------------------------------------------------------------
# Insert idempotent (IntegrityError -> dedupe)
# ------------------------------------------------------------
def _insert_respuesta_or_return_existing(
    *,
    sesion_id: int,
    trial_id: str,
    ccp_code: str,
    sub_code: str,
    is_correct_int,
    tr_ms: int | None,
    mode_to_store: str,
    event_type: str | None,
    is_blank: int,
    idem: str | None,
    answer_flags: dict,
    trial_item_id: str | None,
    user_answer: str | None,
    event_ts: str | None,
    warning: str | None,
):
    has_mode = _table_has_column("tlt_respuesta", "mode")
    has_event_type = _table_has_column("tlt_respuesta", "event_type")
    has_is_blank = _table_has_column("tlt_respuesta", "is_blank")
    has_trial_id = _table_has_column("tlt_respuesta", "trial_id")
    has_idem_col = _table_has_column("tlt_respuesta", "idempotency_key")

    has_item_id = _table_has_column("tlt_respuesta", "item_id")
    has_respuesta = _table_has_column("tlt_respuesta", "respuesta")
    has_event_ts = _table_has_column("tlt_respuesta", "event_ts")
    has_answer_flags = _table_has_column("tlt_respuesta", "answer_flags")

    cols = ["sesion_id", "ccp_code", "ejer_code", "correcta", "tr_ms"]
    vals = ["%s", "%s", "%s", "%s", "%s"]
    params = [sesion_id, ccp_code, sub_code, is_correct_int, tr_ms]

    if has_trial_id:
        cols.append("trial_id")
        vals.append("%s")
        params.append(trial_id)

    if has_item_id:
        cols.append("item_id")
        vals.append("%s")
        params.append(trial_item_id)

    if has_respuesta:
        cols.append("respuesta")
        vals.append("%s")
        params.append(user_answer)

    if has_idem_col:
        cols.append("idempotency_key")
        vals.append("%s")
        params.append(idem)

    if has_mode:
        cols.append("mode")
        vals.append("%s")
        params.append(mode_to_store)

    if has_event_type:
        cols.append("event_type")
        vals.append("%s")
        params.append(event_type)

    if has_event_ts:
        if event_ts is None:
            cols.append("event_ts")
            vals.append("CURRENT_TIMESTAMP")
        else:
            cols.append("event_ts")
            vals.append("%s")
            params.append(event_ts)

    if has_is_blank:
        cols.append("is_blank")
        vals.append("%s")
        params.append(is_blank)

    if has_answer_flags:
        cols.append("answer_flags")
        vals.append("%s")
        params.append(json.dumps(answer_flags or {}, ensure_ascii=False))

    cols.append("created_at")
    vals.append("CURRENT_TIMESTAMP")

    sql = f"INSERT INTO tlt_respuesta ({', '.join(cols)}) VALUES ({', '.join(vals)})"

    try:
        with connection.cursor() as cur:
            cur.execute(sql, params)

    except IntegrityError:
        _metric_inc("answer_deduped", 1)

        for delay in (0.0, 0.01, 0.05, 0.1):
            if delay:
                time.sleep(delay)

            resp = _try_answer_dedupe_by_mode(
                sesion_id=int(sesion_id),
                trial_id=str(trial_id),
                idempotency_key=idem,
            )
            if resp is not None:
                return resp

        # Si llegas aquí, estado inconsistente: NO devuelvas ok=true.
        return JsonResponse(
            {
                "error": "idempotency_dedupe_failed",
                "detail": "IntegrityError but no row found after retries",
                "sesion_id": int(sesion_id),
                "trial_id": str(trial_id),
                "idempotency_key": idem,
            },
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )

    payload = _build_answer_payload(
        sesion_id=int(sesion_id),
        trial_id=str(trial_id),
        item_id=trial_item_id,
        ccp_code=(ccp_code or "").strip().upper(),
        sub_code=(sub_code or "").strip().upper(),
        mode=(mode_to_store or "training"),
        correcta=is_correct_int,
        idempotency_key=idem,
        deduped=False,
        warning=warning,
        flags=(answer_flags if isinstance(answer_flags, dict) else {}),
    )
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})