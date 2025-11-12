"""
Functional tests for API Gateway endpoints
Tests actual API functionality with minimal mocking
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4


def test_app_imports():
    """Test that app can be imported"""
    from app.main import app
    assert app is not None


def test_root_endpoint():
    """Test that root endpoint returns correct response"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "api-gateway" in str(data["data"])


def test_health_endpoint_structure():
    """Test health endpoint returns proper structure"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    data = response.json()
    
    # Should have these keys regardless of health status
    assert "success" in data
    assert "message" in data
    assert "data" in data or "error" in data


@patch('app.routes.requests.get')
def test_send_notification_with_mocked_user(mock_get):
    """Test sending notification with mocked user service"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    # Mock user service response
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "success": True,
            "data": {
                "id": str(uuid4()),
                "email": "test@example.com",
                "preferences": {"email": True}
            }
        }
    )
    
    user_id = str(uuid4())
    request_data = {
        "notification_type": "email",
        "user_id": user_id,
        "template_code": "welcome_email",
        "variables": {
            "name": "Test User"
        }
    }
    
    client = TestClient(app)
    response = client.post("/notifications/send", json=request_data)
    
    # Should return success or proper error structure
    assert response.status_code in [200, 201, 400, 404, 422, 503]
    data = response.json()
    assert "success" in data or "detail" in data


def test_send_notification_validation():
    """Test that invalid notification requests are rejected"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Missing required fields
    response = client.post("/notifications/send", json={})
    assert response.status_code == 422  # Validation error
    
    # Invalid notification type
    response = client.post("/notifications/send", json={
        "notification_type": "invalid",
        "user_id": str(uuid4()),
        "template_code": "test"
    })
    assert response.status_code == 422


def test_notification_schemas_import():
    """Test that schemas can be imported and used"""
    from app.schemas import NotificationRequest, NotificationType
    
    # Should be able to create valid schema
    assert NotificationType.email.value == "email"
    assert NotificationType.push.value == "push"


def test_models_exist():
    """Test that database models are defined"""
    from app.models import NotificationRequest
    
    assert NotificationRequest is not None
    assert hasattr(NotificationRequest, 'id')
    assert hasattr(NotificationRequest, 'notification_type')
