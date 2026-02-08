// lib/api/api_client.dart

import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'r1_envelope.dart';

class ApiClient {
  final Uri baseUri;
  final http.Client _http;
  final Duration timeout;

  ApiClient({
    required this.baseUri,
    http.Client? httpClient,
    this.timeout = const Duration(seconds: 10),
  }) : _http = httpClient ?? http.Client();

  void close() => _http.close();

  Uri _u(String path, [Map<String, String>? query]) {
    return baseUri.replace(
      path: _joinPath(baseUri.path, path),
      queryParameters: (query == null || query.isEmpty) ? null : query,
    );
  }

  static String _joinPath(String a, String b) {
    final aa = a.endsWith('/') ? a.substring(0, a.length - 1) : a;
    final bb = b.startsWith('/') ? b.substring(1) : b;
    if (aa.isEmpty) return '/$bb';
    return '$aa/$bb';
  }

  Map<String, String> _headers({
    String? sessionId,
    String? idempotencyKey,
  }) {
    return <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (sessionId != null && sessionId.isNotEmpty) 'X-Session-Id': sessionId,
      if (idempotencyKey != null && idempotencyKey.isNotEmpty)
        'Idempotency-Key': idempotencyKey,
    };
  }

  Future<R1Envelope<T>> get<T>(
    String path, {
    Map<String, String>? query,
    String? sessionId,
    T Function(Object? dataJson)? decodeData,
  }) async {
    final resp = await _http
        .get(_u(path, query), headers: _headers(sessionId: sessionId))
        .timeout(timeout);

    return _parseEnvelope<T>(resp, decodeData: decodeData);
  }

  Future<R1Envelope<T>> post<T>(
    String path, {
    Object? body,
    Map<String, String>? query,
    String? sessionId,
    String? idempotencyKey,
    T Function(Object? dataJson)? decodeData,
  }) async {
    final resp = await _http
        .post(
          _u(path, query),
          headers: _headers(sessionId: sessionId, idempotencyKey: idempotencyKey),
          body: jsonEncode(body ?? const <String, dynamic>{}),
        )
        .timeout(timeout);

    return _parseEnvelope<T>(resp, decodeData: decodeData);
  }

  /// Retry policy: ONLY for /ccp/next and ONLY for transient failures.
  Future<R1Envelope<T>> getNextWithRetry<T>(
    String path, {
    Map<String, String>? query,
    String? sessionId,
    int maxAttempts = 2,
    Duration backoff = const Duration(milliseconds: 250),
    T Function(Object? dataJson)? decodeData,
  }) async {
    int attempt = 0;
    while (true) {
      attempt += 1;
      try {
        return await get<T>(
          path,
          query: query,
          sessionId: sessionId,
          decodeData: decodeData,
        );
      } on TimeoutException {
        if (attempt >= maxAttempts) rethrow;
      } on http.ClientException {
        if (attempt >= maxAttempts) rethrow;
      }
      await Future<void>.delayed(backoff);
    }
  }

  R1Envelope<T> _parseEnvelope<T>(
    http.Response resp, {
    T Function(Object? dataJson)? decodeData,
  }) {
    final decoded = jsonDecode(resp.body);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Envelope is not a JSON object');
    }
    return R1Envelope.fromJson<T>(decoded, decodeData: decodeData);
  }
}