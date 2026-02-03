"""
API Dependencies
JWT authentication, tenant isolation, and common dependencies
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.db.session import get_db
from app.core.auth import JWTHandler, TokenPayload, PermissionChecker, TenantValidator
from app.utils.errors import AuthenticationError, AuthorizationError
from app.config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

# Demo mode constants
DEMO_TOKEN = "demo_hackathon_token_2026"
DEMO_USER_PAYLOAD = TokenPayload(
    sub="demo_user",
    tenant_id="demo_tenant",
    username="demo_user",
    email="demo@hackathon.local",
    permissions=["zkpa:generate", "zkpa:verify", "zkpa:revoke", "zkpa:admin"]
)


async def get_current_user_demo(
    authorization: Optional[str] = Header(None)
) -> TokenPayload:
    """
    Demo mode authentication - accepts any token or no token
    
    Returns:
        Demo user payload
    """
    if authorization and "Bearer" in authorization:
        # Accept any token in demo mode
        logger.debug(f"Demo mode: Accepting authorization header")
    else:
        logger.debug(f"Demo mode: No auth required")
    
    return DEMO_USER_PAYLOAD


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """
    Extract and validate JWT token from request
    
    Returns:
        TokenPayload with user info
        
    Raises:
        HTTPException: If authentication fails
    """
    # Demo mode bypass
    if settings.DEMO_MODE and not settings.get("REQUIRE_AUTH", False):
        logger.debug("Demo mode enabled - using demo user")
        return DEMO_USER_PAYLOAD
    
    try:
        token = credentials.credentials
        payload = JWTHandler.verify_token(token)
        return payload
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function
    """
    async def permission_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        try:
            PermissionChecker.require_permission(current_user.permissions, permission)
            return current_user
        except AuthorizationError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
    return permission_checker


async def require_generate_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:generate permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.GENERATE)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def require_verify_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:verify permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.VERIFY)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def require_revoke_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:revoke permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.REVOKE)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def require_admin_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:admin permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.ADMIN)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def require_attest_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:attest permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.GENERATE)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def require_publish_permission(
    current_user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require zkpa:publish permission"""
    try:
        PermissionChecker.require_permission(current_user.permissions, PermissionChecker.GENERATE)
        return current_user
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


def validate_tenant_access(resource_tenant_id: str, current_user: TokenPayload):
    """
    Validate user has access to resource
    
    Args:
        resource_tenant_id: Tenant ID of the resource
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If tenant mismatch
    """
    try:
        TenantValidator.validate_tenant_access(current_user.tenant_id, resource_tenant_id)
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


async def get_request_id(x_request_id: Optional[str] = Header(None)) -> str:
    """
    Get or generate request ID for tracing
    
    Args:
        x_request_id: Request ID from header
        
    Returns:
        Request ID
    """
    import uuid
    return x_request_id or str(uuid.uuid4())


class RateLimiter:
    """
    Simple in-memory rate limiter
    (In production, use Redis-based rate limiting)
    """
    def __init__(self):
        self.requests = {}
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit
        
        Args:
            key: Rate limit key (e.g., user_id)
            limit: Max requests
            window: Time window in seconds
            
        Returns:
            True if within limit
        """
        import time
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < window]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Rate limiting dependency
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not rate_limiter.check_rate_limit(
        current_user.sub,
        limit=60,  # 60 requests
        window=60  # per minute
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 60 requests per minute.",
            headers={"Retry-After": "60"}
        )
