#!/usr/bin/env python3
"""
Authentication module for ElevenLabs-compatible API
"""

from typing import Optional, List
from fastapi import Header, HTTPException, status
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages API key authentication"""
    
    def __init__(self, require_auth: bool = False):
        """
        Initialize auth manager
        
        Args:
            require_auth: If True, API key is required. If False, optional.
        """
        self.require_auth = require_auth
        self.valid_keys = set()  # In production, load from database/config
    
    def add_api_key(self, api_key: str):
        """Add a valid API key"""
        self.valid_keys.add(api_key)
    
    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """
        Validate API key
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid or auth not required, False otherwise
        """
        if not self.require_auth:
            return True
        
        if not api_key:
            return False
        
        return api_key in self.valid_keys


# Global auth manager instance (will be initialized on startup)
auth_manager: Optional[AuthManager] = None


def initialize_auth(require_auth: bool = False, api_keys: List[str] = None):
    """
    Initialize authentication system
    
    Args:
        require_auth: Whether to require authentication
        api_keys: List of valid API keys
    """
    global auth_manager
    auth_manager = AuthManager(require_auth=require_auth)
    
    if api_keys:
        for key in api_keys:
            auth_manager.add_api_key(key)
        logger.info(f"✓ Authentication initialized: require_auth={require_auth}, {len(api_keys)} key(s) loaded")
    else:
        logger.info(f"✓ Authentication initialized: require_auth={require_auth}, no keys configured")


def get_api_key(xi_api_key: Optional[str] = Header(None, alias="xi-api-key")) -> Optional[str]:
    """
    Extract API key from request header
    
    Args:
        xi_api_key: API key from xi-api-key header
        
    Returns:
        API key or None
    """
    return xi_api_key


def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_key = kwargs.get('xi_api_key') or kwargs.get('api_key')
        
        if auth_manager.require_auth and not auth_manager.validate_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Please provide a valid xi-api-key header."
            )
        
        return await func(*args, **kwargs)
    return wrapper

