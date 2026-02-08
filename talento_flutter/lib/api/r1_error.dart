// lib/api/r1_error.dart

class R1Error {
  final String code;
  final String? message;
  final Map<String, dynamic>? details;

  const R1Error({
    required this.code,
    this.message,
    this.details,
  });

  factory R1Error.fromJson(Map<String, dynamic> json) {
    final code = (json['code'] ?? '').toString().trim();
    return R1Error(
      code: code.isEmpty ? 'internal_error' : code,
      message: json['message'] is String ? json['message'] as String : null,
      details: json['details'] is Map<String, dynamic>
          ? (json['details'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'code': code,
        if (message != null) 'message': message,
        if (details != null) 'details': details,
      };
}