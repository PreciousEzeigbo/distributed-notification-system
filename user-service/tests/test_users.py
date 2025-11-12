"""
Simple functional tests for User Service
Tests basic imports and structure
"""
import pytest


def test_app_imports():
    """Test that app can be imported"""
    from app.main import app
    assert app is not None


def test_models_import():
    """Test that models can be imported"""
    from app.models import User
    assert User is not None


def test_schemas_import():
    """Test that schemas can be imported"""
    from app.schemas import UserCreate, UserResponse
    assert UserCreate is not None
    assert UserResponse is not None


def test_config_import():
    """Test that config can be imported"""
    from app import config
    assert config.SECRET_KEY is not None
    assert config.DATABASE_URL is not None


def test_database_import():
    """Test that database module can be imported"""
    from app.database import Base, engine
    assert Base is not None
    assert engine is not None


def test_routes_import():
    """Test that routes can be imported"""
    from app import routes
    assert routes is not None
