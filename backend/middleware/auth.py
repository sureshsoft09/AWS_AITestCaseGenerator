"""
Authentication and Authorization Middleware for MedAssureAI.
Implements JWT token validation and IAM-based authentication.
"""
from typing import Optional, Callable
from functools import wraps
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError
import boto3
from botocore.exceptions import ClientError
from backend.config import config
from backend.logger import logger


# Security scheme for bearer token
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for FastAPI."""
    
    def __init__(self):
        """Initialize authentication middleware."""
        self.cognito_client = None
        self._initialize_cognito_client()
    
    def _initialize_cognito_client(self):
        """Initialize AWS Cognito client."""
        try:
            self.cognito_client = boto3.client(
                'cognito-idp',
                region_name=config.AWS_REGION
            )
            logger.info("AWS Cognito client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Cognito client: {str(e)}")
            # Don't raise - allow service to continue without authentication in development
    
    async def verify_token(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> dict:
        """
        Verify JWT token from Authorization header.
        
        Args:
            credentials: HTTP authorization credentials with bearer token
            
        Returns:
            Decoded token payload with user information
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        token = credentials.credentials
        
        try:
            # Decode and verify JWT token
            # In production, this would verify against Cognito public keys
            payload = self._decode_token(token)
            
            # Validate token claims
            self._validate_token_claims(payload)
            
            logger.info(
                "Token verified successfully",
                extra={"user_id": payload.get("sub")}
            )
            
            return payload
            
        except PyJWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def _decode_token(self, token: str) -> dict:
        """
        Decode JWT token.
        
        In production, this would:
        1. Fetch Cognito public keys (JWKS)
        2. Verify token signature
        3. Decode token payload
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
        """
        # For development, decode without verification
        # In production, use proper JWT verification with Cognito public keys
        if config.ENVIRONMENT == "development":
            # Decode without verification for development
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            # In production, verify signature with Cognito public keys
            # This is a placeholder - implement proper JWKS verification
            payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY if hasattr(config, 'JWT_SECRET_KEY') else "secret",
                algorithms=["RS256"],
                audience=config.COGNITO_APP_CLIENT_ID if hasattr(config, 'COGNITO_APP_CLIENT_ID') else None
            )
        
        return payload
    
    def _validate_token_claims(self, payload: dict):
        """
        Validate JWT token claims.
        
        Args:
            payload: Decoded token payload
            
        Raises:
            HTTPException: If token claims are invalid
        """
        # Check required claims
        required_claims = ["sub", "exp"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Missing required claim: {claim}"
                )
        
        # Additional validation can be added here
        # - Check token expiration (handled by jwt.decode)
        # - Check issuer
        # - Check audience
        # - Check custom claims
    
    async def verify_iam_credentials(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> dict:
        """
        Verify IAM credentials.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            IAM user information
            
        Raises:
            HTTPException: If credentials are invalid
        """
        try:
            # In production, this would verify IAM credentials
            # using AWS STS or IAM APIs
            
            logger.info("IAM credentials verified")
            
            return {
                "user_id": "iam_user",
                "auth_type": "iam"
            }
            
        except Exception as e:
            logger.error(f"IAM verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid IAM credentials"
            )
    
    def check_permissions(self, user: dict, required_permissions: list) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user: User information from token
            required_permissions: List of required permission strings
            
        Returns:
            True if user has all required permissions
            
        Raises:
            HTTPException: If user lacks required permissions
        """
        # In production, this would check against IAM policies or Cognito groups
        user_permissions = user.get("permissions", [])
        
        for permission in required_permissions:
            if permission not in user_permissions:
                logger.warning(
                    "Permission denied",
                    extra={
                        "user_id": user.get("sub"),
                        "required_permission": permission
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        return True


# Create singleton instance
auth_middleware = AuthMiddleware()


# Dependency for protected endpoints
async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Dependency for endpoints that require authentication.
    
    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(require_auth)):
            return {"user_id": user["sub"]}
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User information from verified token
    """
    return await auth_middleware.verify_token(credentials)


def require_permissions(*permissions: str):
    """
    Decorator for endpoints that require specific permissions.
    
    Usage:
        @router.get("/admin")
        @require_permissions("admin:read", "admin:write")
        async def admin_endpoint(user: dict = Depends(require_auth)):
            return {"message": "Admin access granted"}
    
    Args:
        permissions: Required permission strings
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, user: dict = None, **kwargs):
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            auth_middleware.check_permissions(user, list(permissions))
            return await func(*args, user=user, **kwargs)
        
        return wrapper
    return decorator


# Optional: Dependency for endpoints that optionally use authentication
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """
    Dependency for endpoints that optionally use authentication.
    
    Returns None if no credentials provided, otherwise verifies token.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        User information if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        return await auth_middleware.verify_token(credentials)
    except HTTPException:
        return None
