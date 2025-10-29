"""Authentication and validation middleware"""

import logging
from typing import Optional
from fastapi import HTTPException, Header
from .config import config_manager

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self):
        self.config = config_manager.get_config()
        self.api_key = self.config.api_key
    
    def validate_api_key(self, authorization: Optional[str] = Header(None)) -> bool:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")
        
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authorization scheme")
            if token != self.api_key:
                raise HTTPException(status_code=401, detail="Invalid API key")
            return True
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    def validate_websocket_token(self, token: Optional[str]) -> bool:
        return token == self.api_key if token else False


class RequestValidator:
    def __init__(self):
        self.config = config_manager.get_config()
    
    def validate_language(self, language: str):
        from .config import LanguageCode
        try:
            return LanguageCode(language)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid language: {language}")


auth_manager = AuthManager()
request_validator = RequestValidator()

