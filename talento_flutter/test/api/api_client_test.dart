import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:talento_flutter/api/api_client.dart';
import 'package:talento_flutter/api/endpoints.dart';

void main() {
  test('ApiClient parses R1Envelope from GET', () async {
    final mock = MockClient((req) async {
      expect(req.url.path, Endpoints.health);
      return http.Response(
        jsonEncode({
          'ok': true,
          'data': {'status': 'ok'},
          'meta': {'contract_version': 'r1'},
        }),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final api = ApiClient(
      baseUri: Uri.parse('http://localhost:8000'),
      httpClient: mock,
    );

    final env = await api.get<Map<String, dynamic>>(Endpoints.health);
    expect(env.isOk, true);
    expect(env.data?['status'], 'ok');
    expect(env.meta['contract_version'], 'r1');
  });

  test('ApiClient sends X-Session-Id and Idempotency-Key on POST', () async {
    final mock = MockClient((req) async {
      expect(req.headers['X-Session-Id'], '123');
      expect(req.headers['Idempotency-Key'], 'idem-1');
      return http.Response(
        jsonEncode({'ok': true, 'data': {}, 'meta': {}}),
        200,
        headers: {'content-type': 'application/json'},
      );
    });

    final api = ApiClient(
      baseUri: Uri.parse('http://localhost:8000'),
      httpClient: mock,
    );

    final env = await api.post<Map<String, dynamic>>(
      Endpoints.ccpAnswer,
      sessionId: '123',
      idempotencyKey: 'idem-1',
      body: {'x': 1},
    );
    expect(env.isOk, true);
  });
}