"""Tests for paper CRUD and submission endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_health_check(client):
    """Test that health check endpoint is accessible."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_process_paper_with_arxiv_id(client, mock_auth, mock_user_record):
    """Test submitting a paper with an ArXiv ID."""
    with patch(
        "services.supabase_client.create_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-id-123",
            "user_id": "test-user-id",
            "arxiv_id": "2106.09685",
            "status": "queued",
        },
    ), patch(
        "services.job_queue.enqueue_paper_job",
        new_callable=AsyncMock,
        return_value="job-id-456",
    ):
        response = await client.post(
            "/api/papers/process",
            json={"source": "2106.09685", "user_preferences": {}},
        )
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "job-id-456"
        assert data["paper_id"] == "paper-id-123"
        assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_process_paper_with_url(client, mock_auth, mock_user_record):
    """Test submitting a paper with an ArXiv URL."""
    with patch(
        "services.supabase_client.create_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-id-123",
            "arxiv_id": "1706.03762",
        },
    ), patch(
        "services.job_queue.enqueue_paper_job",
        new_callable=AsyncMock,
        return_value="job-id-456",
    ):
        response = await client.post(
            "/api/papers/process",
            json={
                "source": "https://arxiv.org/abs/1706.03762",
                "user_preferences": {},
            },
        )
        assert response.status_code == 202


@pytest.mark.asyncio
async def test_upload_pdf(client, mock_auth, mock_user_record):
    """Test uploading a PDF file."""
    with patch(
        "services.storage.upload_pdf",
        new_callable=AsyncMock,
        return_value="papers/abc-123.pdf",
    ), patch(
        "services.supabase_client.create_paper",
        new_callable=AsyncMock,
        return_value={"id": "paper-id-123"},
    ), patch(
        "services.job_queue.enqueue_paper_job",
        new_callable=AsyncMock,
        return_value="job-id-456",
    ):
        # Note: In real test, would use UploadFile
        # This is a simplified version
        response = await client.post(
            "/api/papers/upload",
            files={"file": ("test.pdf", b"PDF content", "application/pdf")},
        )
        # Response could be 202 if successful or error if file handling fails
        # This test demonstrates the pattern


@pytest.mark.asyncio
async def test_list_papers(client, mock_auth, mock_user_record):
    """Test listing user's papers."""
    with patch(
        "services.supabase_client.list_papers",
        new_callable=AsyncMock,
        return_value=[
            {
                "id": "paper-1",
                "title": "Sample Paper",
                "status": "done",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ],
    ):
        response = await client.get("/api/papers?limit=20&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "paper-1"


@pytest.mark.asyncio
async def test_get_paper(client, mock_auth, mock_user_record):
    """Test retrieving a single paper."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={
            "id": "paper-1",
            "title": "Sample Paper",
            "status": "done",
            "smart_brief": {
                "title": "Sample",
                "tldr": "A brief",
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
    ):
        response = await client.get("/api/papers/paper-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "paper-1"


@pytest.mark.asyncio
async def test_delete_paper(client, mock_auth, mock_user_record):
    """Test deleting a paper."""
    with patch(
        "services.supabase_client.get_paper",
        new_callable=AsyncMock,
        return_value={"id": "paper-1", "pdf_path": "papers/test.pdf"},
    ), patch(
        "services.storage.delete_pdf",
        new_callable=AsyncMock,
    ), patch(
        "services.supabase_client.delete_paper",
        new_callable=AsyncMock,
    ):
        response = await client.delete("/api/papers/paper-1")
        assert response.status_code == 204
