"""Test configuration and fixtures."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app


@pytest.fixture
async def client():
    """Create a test AsyncClient for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
def mock_auth():
    """Mock JWT verification — returns a test user."""

    def mock_get_current_user():
        return {
            "id": "test-user-id",
            "email": "test@example.com",
            "plan": "pro",
        }

    with patch(
        "core.security.get_current_user",
        new_callable=AsyncMock,
        return_value={
            "id": "test-user-id",
            "email": "test@example.com",
            "plan": "pro",
        },
    ):
        yield


@pytest.fixture
def mock_user_record():
    """Mock user database record."""

    def mock_get_or_create_user():
        return {
            "id": "test-user-db-id",
            "supabase_auth_id": "test-user-id",
            "email": "test@example.com",
            "plan": "pro",
        }

    with patch(
        "services.supabase_client.get_or_create_user",
        new_callable=AsyncMock,
        return_value={
            "id": "test-user-db-id",
            "supabase_auth_id": "test-user-id",
            "email": "test@example.com",
            "plan": "pro",
        },
    ):
        yield
