"""Tests for SSE streaming endpoint."""
import pytest
import json
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_stream_connection(client, mock_auth, mock_user_record):
    """Test SSE connection is established."""
    with patch(
        "services.redis_client.get_redis",
        new_callable=AsyncMock,
    ) as mock_redis:
        mock_pubsub = AsyncMock()
        mock_redis.return_value.pubsub.return_value = mock_pubsub

        # Mock an async generator for pubsub.listen()
        async def mock_listen():
            yield {"type": "message", "data": json.dumps({"type": "progress"})}

        mock_pubsub.listen.return_value = mock_listen()

        with patch(
            "services.redis_client.get_job_status",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.get("/api/stream/job-123")
            # SSE should return 200
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
