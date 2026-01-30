"""
Custom Exception Classes
Application-specific exceptions for better error handling
"""


class ZKPAException(Exception):
    """Base exception for ZKPA"""
    def __init__(self, message: str, error_code: str = "ZKPA_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(ZKPAException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(ZKPAException):
    """Authorization failed - insufficient permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHZ_ERROR")


class TenantIsolationError(ZKPAException):
    """Tenant isolation violation"""
    def __init__(self, message: str = "Tenant isolation violation"):
        super().__init__(message, "TENANT_ERROR")


class ValidationError(ZKPAException):
    """Input validation error"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(ZKPAException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        self.resource = resource
        self.identifier = identifier
        super().__init__(message, "NOT_FOUND")


class ConflictError(ZKPAException):
    """Resource conflict (e.g., already exists)"""
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")


class EvidenceError(ZKPAException):
    """Evidence processing error"""
    def __init__(self, message: str):
        super().__init__(message, "EVIDENCE_ERROR")


class ProofGenerationError(ZKPAException):
    """Proof generation failed"""
    def __init__(self, message: str, circuit_id: str = None):
        self.circuit_id = circuit_id
        super().__init__(message, "PROOF_ERROR")


class VerificationError(ZKPAException):
    """Proof verification failed"""
    def __init__(self, message: str):
        super().__init__(message, "VERIFICATION_ERROR")


class AnchoringError(ZKPAException):
    """Blockchain anchoring error"""
    def __init__(self, message: str):
        super().__init__(message, "ANCHORING_ERROR")


class StorageError(ZKPAException):
    """Storage operation failed"""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class CryptoError(ZKPAException):
    """Cryptographic operation failed"""
    def __init__(self, message: str):
        super().__init__(message, "CRYPTO_ERROR")


class SignatureError(ZKPAException):
    """Digital signature operation failed"""
    def __init__(self, message: str):
        super().__init__(message, "SIGNATURE_ERROR")


class RateLimitExceeded(ZKPAException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds", "RATE_LIMIT")


class ExternalServiceError(ZKPAException):
    """External service call failed"""
    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"{service} error: {message}", "EXTERNAL_SERVICE_ERROR")
