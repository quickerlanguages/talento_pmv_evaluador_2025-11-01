// lib/api/r1_envelope.dart

import 'r1_error.dart';

/// Canonical API envelope for Talento Mobile Contract R1.
///
/// OK:
///   { ok:true,  data:{...},  meta:{...} }
/// ERR:
///   { ok:false, error:{code,...}, meta:{...} }
class R1Envelope<T> {
  final bool ok;
  final T? data;
  final R1Error? error;
  final Map<String, dynamic> meta;

  const R1Envelope._({
    required this.ok,
    required this.data,
    required this.error,
    required this.meta,
  });

  bool get isOk => ok == true;

  /// Parse an envelope and optionally parse data with [decodeData].
  ///
  /// If ok=true and data missing -> data becomes null (caller decides).
  /// If ok=false and error missing -> error becomes internal_error.
  static R1Envelope<T> fromJson<T>(
    Map<String, dynamic> json, {
    T Function(Object? dataJson)? decodeData,
  }) {
    final okVal = json['ok'];
    final ok = okVal == true;

    final metaRaw = json['meta'];
    final meta = metaRaw is Map<String, dynamic>
        ? metaRaw
        : <String, dynamic>{};

    if (ok) {
      final raw = json['data'];
      final parsed = decodeData != null ? decodeData(raw) : raw as T?;
      return R1Envelope._(
        ok: true,
        data: parsed,
        error: null,
        meta: meta,
      );
    }

    // ok=false
    final errRaw = json['error'];
    final err = errRaw is Map<String, dynamic>
        ? R1Error.fromJson(errRaw)
        : const R1Error(code: 'internal_error');

    return R1Envelope._(
      ok: false,
      data: null,
      error: err,
      meta: meta,
    );
  }
}