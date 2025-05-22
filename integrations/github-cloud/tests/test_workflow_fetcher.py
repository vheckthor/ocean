import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.fetchers.workflow import WorkflowFetcher
from githubcloud.clients.github_client import GitHubClient

@pytest.fixture
def mock_event_context():
    with patch("port_ocean.context.event._event_context_stack") as mock_stack:
        mock_context = MagicMock(spec=EventContext)
        mock_context.attributes = {}
        mock_stack.top = mock_context
        yield mock_context

@pytest.fixture
def mock_http_client():
    client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.headers = {"X-RateLimit-Remaining": "1000"}
    mock_response.json = AsyncMock(return_value=[])
    client.request.return_value = mock_response
    return client

@pytest.fixture
def github_client(mock_http_client):
    return GitHubClient("test-token", mock_http_client)

@pytest.fixture
def workflow_fetcher(github_client):
    return WorkflowFetcher(github_client)

@pytest.mark.asyncio
async def test_fetch_workflows(workflow_fetcher, mock_http_client, mock_event_context):
    mock_response = [
        {
            "id": 1,
            "name": "test-workflow",
            "path": ".github/workflows/test.yml",
            "state": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "html_url": "https://github.com/test-org/test-repo/actions/workflows/test.yml",
            "node_id": "test-node-id",
            "repository": {
                "id": 1,
                "name": "test-repo",
                "full_name": "test-org/test-repo"
            }
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    entities = []
    async for entity in workflow_fetcher.fetch("test-org", "test-repo"):
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0]["identifier"] == "1"
    assert entities[0]["title"] == "test-workflow"
    assert entities[0]["url"] == "https://github.com/test-org/test-repo/actions/workflows/test.yml"
    assert entities[0]["properties"]["path"] == ".github/workflows/test.yml"
    assert entities[0]["properties"]["state"] == "active"
    assert entities[0]["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert entities[0]["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["properties"]["nodeId"] == "test-node-id"
    assert entities[0]["relations"]["repository"]["title"] == "test-repo"
    assert entities[0]["relations"]["repository"]["identifier"] == "1"

    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"
    assert "/repos/test-org/test-repo/actions/workflows" in call_args[0][1]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
