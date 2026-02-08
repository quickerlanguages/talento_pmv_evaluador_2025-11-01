import 'package:flutter_test/flutter_test.dart';
import 'package:talento_flutter/api/r1_envelope.dart';

void main() {
  test('R1Envelope parses ok=true with meta', () {
    final json = <String, dynamic>{
      'ok': true,
      'data': {'sesion_id': 123},
      'meta': {'contract_version': 'r1'},
    };

    final env = R1Envelope.fromJson<Map<String, dynamic>>(json);
    expect(env.isOk, true);
    expect(env.data?['sesion_id'], 123);
    expect(env.error, isNull);
    expect(env.meta['contract_version'], 'r1');
  });

  test('R1Envelope parses ok=false with error', () {
    final json = <String, dynamic>{
      'ok': false,
      'error': {'code': 'invalid_request', 'message': 'bad'},
      'meta': {'contract_version': 'r1'},
    };

    final env = R1Envelope.fromJson<Map<String, dynamic>>(json);
    expect(env.isOk, false);
    expect(env.data, isNull);
    expect(env.error, isNotNull);
    expect(env.error!.code, 'invalid_request');
    expect(env.error!.message, 'bad');
  });

  test('R1Envelope ok=false without error becomes internal_error', () {
    final json = <String, dynamic>{
      'ok': false,
      'meta': {'contract_version': 'r1'},
    };

    final env = R1Envelope.fromJson<Object?>(json);
    expect(env.isOk, false);
    expect(env.error, isNotNull);
    expect(env.error!.code, 'internal_error');
  });

  test('R1Envelope ok=true supports decodeData', () {
    final json = <String, dynamic>{
      'ok': true,
      'data': {'x': 7},
      'meta': {},
    };

    final env = R1Envelope.fromJson<int>(json, decodeData: (raw) {
      final m = raw as Map<String, dynamic>;
      return (m['x'] as num).toInt();
    });

    expect(env.isOk, true);
    expect(env.data, 7);
  });
}