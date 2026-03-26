"""Tests for export generation endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_export_free_plan_blocked(client, mock_auth):
    """Test that free users cannot generate exports."""
    # Mock a free user
    with patch(
        "services.supabase_client.get_or_create_user",
        new_callable=AsyncMock,
        return_value={
            "id": "user-123",
            "plan": "free",
        },
    ):
        response = await client.post(
            "/api/exports",
            json={"paper_id": "paper-1", "format": "podcast_script"},
        )
        # Should be 403 Forbidden
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_pro_plan_success(client, mock_auth, mock_user_record):
    """Test that pro users can generate exports."""
    with patch(
        "services.supabase_client.get_or_create_user",
        new_callable=AsyncMock,
        return_value={
            "id": "user-123",
            "plan": "pro",
        },
    ), patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-1",
            "status": "done",
            "smart_brief": {"title": "Sample", "tldr": "Brief"},
        },
    ), patch(
        "services.supabase_client.save_export",
        new_callable=AsyncMock,
        return_value={
            "id": "export-1",
            "created_at": datetime.utcnow().isoformat(),
        },
    ):
        response = await client.post(
            "/api/exports",
            json={"paper_id": "paper-1", "format": "podcast_script"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "podcast_script"


@pytest.mark.asyncio
async def test_export_paper_not_done(client, mock_auth, mock_user_record):
    """Test exporting a paper that's still processing."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-1",
            "status": "processing",
        },
    ):
        response = await client.post(
            "/api/exports",
            json={"paper_id": "paper-1", "format": "podcast_script"},
        )
        assert response.status_code == 409
