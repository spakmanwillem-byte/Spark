"""
Pytest configuration for Spark backend tests
"""
import os
import pytest


def pytest_configure(config):
    """Set environment variables for testing"""
    # Get backend URL from frontend .env if not already set
    if not os.environ.get('REACT_APP_BACKEND_URL'):
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.strip().split('=', 1)[1]
                        os.environ['REACT_APP_BACKEND_URL'] = backend_url
                        print(f"✅ Set REACT_APP_BACKEND_URL to: {backend_url}")
                        break
        except Exception as e:
            print(f"⚠️ Could not load backend URL from .env: {e}")
