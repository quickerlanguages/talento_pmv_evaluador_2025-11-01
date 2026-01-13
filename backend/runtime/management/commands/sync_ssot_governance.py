import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from runtime.models import SubmodalityGovernanceCache


@dataclass(frozen=True)
class GovernanceRow:
    submod_code: str
    estado_normativo: str  # active | latent | excluded
    risk_class: str | None  # low | medium | high | None
    introduced_in_version: str
    rules_ref: str | None


# Canonical governance mapping for EVAL_CORE_v1_1.
# NOTE: This is OPS-cache governance (fast lookup). SSOT remains the domain DB.
EVAL_CORE_V1_1_DEFAULTS: dict[str, GovernanceRow] = {
    "motriz": GovernanceRow(
        submod_code="motriz",
        estado_normativo="active",
        risk_class="low",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "visual": GovernanceRow(
        submod_code="visual",
        estado_normativo="active",
        risk_class="low",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "auditiva": GovernanceRow(
        submod_code="auditiva",
        estado_normativo="latent",
        risk_class="high",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "vigilancia": GovernanceRow(
        submod_code="vigilancia",
        estado_normativo="active",
        risk_class="medium",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "busqueda_visual": GovernanceRow(
        submod_code="busqueda_visual",
        estado_normativo="active",
        risk_class="low",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "cambio_regla": GovernanceRow(
        submod_code="cambio_regla",
        estado_normativo="active",
        risk_class="medium",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "matriz_no_verbal": GovernanceRow(
        submod_code="matriz_no_verbal",
        estado_normativo="active",
        risk_class="medium",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
    "analogia_simple": GovernanceRow(
        submod_code="analogia_simple",
        estado_normativo="latent",
        risk_class="medium",
        introduced_in_version="EVAL_CORE_v1_1",
        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
    ),
}


def _default_ssot_path() -> Path:
    # backend/ is BASE_DIR; SSOT DB lives at backend/talento_domain/db/talento_ssot.db
    base_dir = Path(getattr(settings, "BASE_DIR"))
    return base_dir / "talento_domain" / "db" / "talento_ssot.db"


class Command(BaseCommand):
    help = "Sync submodality governance (estado/risk/introduced) from SSOT to OPS cache DB."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--ssot",
            default=str(_default_ssot_path()),
            help="Path to SSOT SQLite DB (default: backend/talento_domain/db/talento_ssot.db)",
        )
        parser.add_argument(
            "--normative-version",
            default="EVAL_CORE_v1_1",
            help="Normative version used as source_normative_version (e.g. EVAL_CORE_v1_1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not write to OPS DB; only print what would be upserted.",
        )

    def handle(self, *args, **opts):
        ssot_path = Path(opts["ssot"]).resolve()
        normative_version = str(opts["normative_version"]).strip()
        dry_run = bool(opts["dry_run"])

        self.stdout.write(f"[sync_ssot_governance] ssot={ssot_path}")
        self.stdout.write(
            f"[sync_ssot_governance] target_ops_db={settings.DATABASES['default']['NAME']}"
        )
        self.stdout.write(f"[sync_ssot_governance] source_normative_version={normative_version}")

        if not ssot_path.exists():
            raise FileNotFoundError(
                f"SSOT DB not found: {ssot_path}\n"
                "Hint: expected at backend/talento_domain/db/talento_ssot.db"
            )

        # Read canonical submod codes from SSOT.
        con = sqlite3.connect(str(ssot_path))
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        ssot_codes = [
            r["codigo"]
            for r in cur.execute("SELECT codigo FROM ref_submodalidad ORDER BY id_submod;")
        ]
        con.close()

        now_utc = datetime.now(timezone.utc)

        rows: list[GovernanceRow] = []
        for code in ssot_codes:
            if code in EVAL_CORE_V1_1_DEFAULTS:
                rows.append(EVAL_CORE_V1_1_DEFAULTS[code])
            else:
                # Safe fallback: unknown submods are latent until explicitly governed.
                rows.append(
                    GovernanceRow(
                        submod_code=code,
                        estado_normativo="latent",
                        risk_class=None,
                        introduced_in_version=normative_version,
                        rules_ref="docs/normativa/SUBMODALITY_ACTIVATION_RULES.md",
                    )
                )

        self.stdout.write(f"[sync_ssot_governance] rows={len(rows)} dry_run={dry_run}")

        if dry_run:
            for r in rows:
                self.stdout.write(
                    f"- {r.submod_code}: {r.estado_normativo} risk={r.risk_class or 'n/a'} intro={r.introduced_in_version}"
                )
            return

        for r in rows:
            SubmodalityGovernanceCache.objects.update_or_create(
                submod_code=r.submod_code,
                defaults={
                    "estado_normativo": r.estado_normativo,
                    "risk_class": r.risk_class,
                    "introduced_in_version": r.introduced_in_version,
                    "rules_ref": r.rules_ref,
                    "source_normative_version": normative_version,
                    "synced_at_utc": now_utc,
                },
            )

        self.stdout.write(self.style.SUCCESS("[sync_ssot_governance] OK"))