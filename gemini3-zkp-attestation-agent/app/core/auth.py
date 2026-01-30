"""
Authentication and Authorization
JWT token handling and permission management
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.config import settings
from app.utils.errors import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload:
    """JWT token payload structure"""
    def __init__(self, 
                 sub: str,
                 tenant_id: str,
                 permissions: List[str],
                 exp: Optional[datetime] = None):
        self.sub = sub  # Subject (user ID)
        self.tenant_id = tenant_id
        self.permissions = permissions
        self.exp = exp or datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub": self.sub,
            "tenant_id": self.tenant_id,
            "permissions": self.permissions,
            "exp": self.exp,
            "iat": datetime.utcnow()
        }


class JWTHandler:
    """JWT token creation and validation"""
    
    @staticmethod
    def create_access_token(payload: TokenPayload) -> str:
        """
        Create a JWT access token
        
        Args:
            payload: Token payload
            
        Returns:
            JWT token string
        """
        to_encode = payload.to_dict()
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error: {e}")
            raise AuthenticationError("Invalid or expired token")
    
    @staticmethod
    def verify_token(token: str) -> TokenPayload:
        """
        Verify token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            TokenPayload object
            
        Raises:
            AuthenticationError: If token is invalid
        """
        payload_dict = JWTHandler.decode_token(token)
        
        # Validate required fields
        if "sub" not in payload_dict or "tenant_id" not in payload_dict:
            raise AuthenticationError("Invalid token payload")
        
        return TokenPayload(
            sub=payload_dict["sub"],
            tenant_id=payload_dict["tenant_id"],
            permissions=payload_dict.get("permissions", []),
            exp=payload_dict.get("exp")
        )


class PermissionChecker:
    """Permission checking utilities"""
    
    # Permission scopes
    GENERATE = "zkpa:generate"
    VERIFY = "zkpa:verify"
    REVOKE = "zkpa:revoke"
    ADMIN = "zkpa:admin"
    
    @staticmethod
    def has_permission(user_permissions: List[str], required_permission: str) -> bool:
        """
        Check if user has required permission
        
        Args:
            user_permissions: List of user's permissions
            required_permission: Required permission
            
        Returns:
            True if user has permission
        """
        # Admin has all permissions
        if PermissionChecker.ADMIN in user_permissions:
            return True
        
        return required_permission in user_permissions
    
    @staticmethod
    def require_permission(user_permissions: List[str], required_permission: str):
        """
        Require a specific permission (raises error if not present)
        
        Args:
            user_permissions: List of user's permissions
            required_permission: Required permission
            
        Raises:
            AuthorizationError: If permission not present
        """
        if not PermissionChecker.has_permission(user_permissions, required_permission):
            raise AuthorizationError(
                f"Insufficient permissions. Required: {required_permission}"
            )
    
    @staticmethod
    def require_any_permission(user_permissions: List[str], required_permissions: List[str]):
        """
        Require at least one of the specified permissions
        
        Args:
            user_permissions: List of user's permissions
            required_permissions: List of acceptable permissions
            
        Raises:
            AuthorizationError: If none of the permissions present
        """
        for permission in required_permissions:
            if PermissionChecker.has_permission(user_permissions, permission):
                return
        
        raise AuthorizationError(
            f"Insufficient permissions. Required one of: {', '.join(required_permissions)}"
        )


class PasswordHandler:
    """Password hashing and verification"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)


class TenantValidator:
    """Tenant isolation validation"""
    
    @staticmethod
    def validate_tenant_access(user_tenant_id: str, resource_tenant_id: str):
        """
        Validate user has access to resource's tenant
        
        Args:
            user_tenant_id: User's tenant ID
            resource_tenant_id: Resource's tenant ID
            
        Raises:
            AuthorizationError: If tenant mismatch
        """
        if user_tenant_id != resource_tenant_id:
            raise AuthorizationError(
                "Access denied - resource belongs to different tenant"
            )


def create_token_for_user(user_id: str, tenant_id: str, permissions: List[str]) -> str:
    """
    Convenience function to create a token
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        permissions: List of permissions
        
    Returns:
        JWT token string
    """
    payload = TokenPayload(
        sub=user_id,
        tenant_id=tenant_id,
        permissions=permissions
    )
    return JWTHandler.create_access_token(payload)
