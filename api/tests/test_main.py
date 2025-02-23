"""
Tests for main application module.
"""
from fastapi.testclient import TestClient
from app.main import app, settings

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_cors_middleware():
    """Test CORS middleware configuration."""
    # Test with allowed origin
    origin = "http://localhost"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    # FastAPI's CORSMiddleware reflects back the origin when allow_origins=["*"]
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-methods" in response.headers
    assert "GET" in response.headers["access-control-allow-methods"]
