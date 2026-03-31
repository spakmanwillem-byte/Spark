"""
Spark Auth Module
Handles authentication, sessions, users, and gradaties
"""
from .service import AuthService
from .routes import router as auth_router

__all__ = ['AuthService', 'auth_router']
