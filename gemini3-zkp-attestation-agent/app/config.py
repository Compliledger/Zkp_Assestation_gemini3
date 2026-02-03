"""
Application Configuration
Manages environment variables and application settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
from functools import lru_cache
import json
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": True
    }
    
    # Application
    APP_NAME: str = "zkpa"
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "info"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", 8000))  # Railway provides PORT env var
    WORKERS: int = 4
    RELOAD: bool = False  # Disable reload in production
    
    # Database
    # Railway automatically provides DATABASE_URL for PostgreSQL plugin
    _DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://zkpa_user:zkpa_password@localhost:5432/zkpa_dev"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Convert Railway's postgresql:// URL to postgresql+asyncpg:// format
        Railway provides DATABASE_URL as postgresql://, but we need postgresql+asyncpg://
        """
        url = self._DATABASE_URL
        if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    
    # Security - JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Security - Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-here"
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    KMS_PROVIDER: str = "local"  # local, aws, azure, vault
    KMS_AWS_REGION: Optional[str] = None
    KMS_AWS_KEY_ID: Optional[str] = None
    KMS_AZURE_VAULT_URL: Optional[str] = None
    KMS_AZURE_KEY_NAME: Optional[str] = None
    
    # Storage
    STORAGE_BACKEND: str = "local"  # local, s3, azure
    STORAGE_BUCKET: str = "zkpa-evidence"
    STORAGE_REGION: str = "us-east-1"
    STORAGE_PATH: str = "./storage"
    EVIDENCE_ENCRYPTION_ENABLED: bool = True
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    
    # Azure Blob
    AZURE_STORAGE_ACCOUNT: Optional[str] = None
    AZURE_STORAGE_KEY: Optional[str] = None
    AZURE_CONTAINER_NAME: Optional[str] = None
    
    # Blockchain Anchoring Service
    ANCHORING_SERVICE_URL: str = "http://localhost:9000"
    ANCHORING_SERVICE_TOKEN: str = "anchoring-service-token"
    ANCHORING_ENABLED: bool = True
    ANCHORING_DEFAULT_CHAIN: str = "ethereum"
    ANCHORING_TIMEOUT: int = 60

    # Algorand (On-Chain)
    ALGORAND_NETWORK: str = "testnet"  # testnet | mainnet
    ALGORAND_API_URL: str = os.environ.get("ALGORAND_API_URL", "https://testnet-api.algonode.cloud")
    ALGORAND_API_TOKEN: str = os.environ.get("ALGORAND_API_TOKEN", "")
    ALGORAND_MNEMONIC: Optional[str] = os.environ.get("ALGORAND_MNEMONIC")
    # Optional: use indexer for lookups; if not set we fall back to algod pending/confirmed tx info.
    ALGORAND_INDEXER_URL: Optional[str] = os.environ.get("ALGORAND_INDEXER_URL")
    # App id of deployed anchoring contract.
    # If not set, /api/v1/anchoring/algorand/contract/deploy can deploy and return an id.
    ALGORAND_ANCHOR_APP_ID: Optional[int] = None
    # Backward compatibility with existing .env values in this repo
    REGISTRY_APP_ID: Optional[int] = None
    
    @field_validator('ALGORAND_ANCHOR_APP_ID', 'REGISTRY_APP_ID', mode='before')
    @classmethod
    def parse_optional_int(cls, v):
        """Parse optional integer fields, converting empty strings to None"""
        if v == '' or v is None:
            return None
        return int(v)
    
    # RMF Engine Integration
    RMF_ENGINE_WEBHOOK_URL: str = "http://localhost:3000/api/webhooks/zkp-callback"
    RMF_ENGINE_AUTH_TOKEN: str = "rmf-engine-token"
    RMF_ENGINE_TIMEOUT: int = 30
    
    # Proof Engine
    PROOF_GENERATION_TIMEOUT: int = 300
    PROOF_VERIFICATION_TIMEOUT: int = 30
    MAX_CONCURRENT_PROOFS: int = 10
    CIRCUIT_CACHE_ENABLED: bool = True
    CIRCUIT_CACHE_TTL: int = 3600
    
    # ZKP Library
    ZKP_LIBRARY: str = "py-zkp"
    CIRCOM_PATH: str = "/usr/local/bin/circom"
    SNARKJS_PATH: str = "/usr/local/bin/snarkjs"
    
    # Evidence Processing
    MAX_EVIDENCE_SIZE_MB: int = 100
    MAX_EVIDENCE_COUNT: int = 1000
    EVIDENCE_COMPRESSION: bool = True
    MERKLE_HASH_ALGORITHM: str = "SHA256"
    
    # Attestation Settings
    DEFAULT_VALIDITY_DAYS: int = 90
    MAX_VALIDITY_DAYS: int = 365
    ATTESTATION_AUTO_EXPIRE: bool = True
    ATTESTATION_RENEWAL_DAYS_BEFORE: int = 30
    
    # Tenant Isolation
    MULTI_TENANT_ENABLED: bool = True
    TENANT_ISOLATION_LEVEL: str = "database"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS
    CORS_ENABLED: bool = True
    CORS_ORIGINS: Union[List[str], str] = '["http://localhost:3000", "http://localhost:3001"]'
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS if it's a string"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
        return self.CORS_ORIGINS
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Prometheus
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    
    # Background Jobs
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    
    # Testing
    TEST_DATABASE_URL: str = "postgresql://zkpa_user:zkpa_password@localhost:5432/zkpa_test"
    MOCK_ANCHORING_SERVICE: bool = False
    MOCK_RMF_ENGINE: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
