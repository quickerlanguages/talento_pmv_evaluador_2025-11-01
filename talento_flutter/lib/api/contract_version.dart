// lib/api/contract_version.dart

/// Single source of truth for the mobile contract version this client expects.
///
/// Must match backend `MOBILE_CONTRACT_VERSION` (R1).
class ContractVersion {
  static const String expected = 'r1';
}