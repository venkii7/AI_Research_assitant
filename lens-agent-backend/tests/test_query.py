"""Tests for Q&A query endpoint."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_query_paper_not_found(client, mock_auth, mock_user_record):
    """Test querying a non-existent paper returns 404."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = await client.post(
            "/api/query",
            json={"paper_id": "nonexistent", "question": "What is this paper?"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_paper_processing(client, mock_auth, mock_user_record):
    """Test querying a paper that's still processing returns 409."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-1",
            "status": "processing",
            "smart_brief": {},
        },
    ):
        response = await client.post(
            "/api/query",
            json={"paper_id": "paper-1", "question": "What is this paper?"},
        )
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_query_paper_success(client, mock_auth, mock_user_record):
    """Test successful query on a processed paper."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-1",
            "status": "done",
            "smart_brief": {
                "title": "Sample Paper",
                "authors": "Authors",
                "year": "2024",
                "tldr": "A brief summary",
                "story": {
                    "problem": "The problem",
                    "method": "The method",
                    "results": "The results",
                    "significance": "The significance",
                },
            },
        },
    ):
        response = await client.post(
            "/api/query",
            json={
                "paper_id": "paper-1",
                "question": "What is the main contribution?",
                "conversation_history": [],
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
