import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.fetchers.issue import IssueFetcher
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
def issue_fetcher(github_client):
    return IssueFetcher(github_client)

@pytest.mark.asyncio
async def test_fetch_issues(issue_fetcher, mock_http_client, mock_event_context):
    mock_response = [
        {
            "id": 1,
            "number": 1,
            "title": "Test Issue",
            "body": "Test issue description",
            "html_url": "https://github.com/test-org/test-repo/issues/1",
            "state": "open",
            "locked": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "comments": 2,
            "labels": [
                {
                    "id": 1,
                    "name": "bug",
                    "color": "d73a4a",
                    "description": "Something isn't working"
                }
            ],
            "assignee": {
                "id": 1,
                "login": "test-user"
            },
            "assignees": [
                {
                    "id": 1,
                    "login": "test-user"
                }
            ],
            "milestone": {
                "id": 1,
                "number": 1,
                "title": "v1.0",
                "description": "Version 1.0",
                "state": "open",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "due_on": "2024-02-01T00:00:00Z"
            },
            "user": {
                "id": 1,
                "login": "test-user"
            },
            "repository": {
                "id": 1,
                "name": "test-repo",
                "full_name": "test-org/test-repo"
            }
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    entities = []
    async for entity in issue_fetcher.fetch("test-org", "test-repo"):
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0]["identifier"] == "1"
    assert entities[0]["title"] == "Test Issue"
    assert entities[0]["url"] == "https://github.com/test-org/test-repo/issues/1"
    assert entities[0]["properties"]["number"] == 1
    assert entities[0]["properties"]["state"] == "open"
    assert entities[0]["properties"]["locked"] is False
    assert entities[0]["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert entities[0]["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["properties"]["closedAt"] is None
    assert entities[0]["properties"]["comments"] == 2
    assert entities[0]["properties"]["labels"] == ["bug"]
    assert entities[0]["properties"]["assignees"] == ["test-user"]
    assert entities[0]["properties"]["milestone"] == "v1.0"
    assert entities[0]["relations"]["author"]["title"] == "test-user"
    assert entities[0]["relations"]["repository"]["title"] == "test-repo"

    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"
    assert "/repos/test-org/test-repo/issues" in call_args[0][1]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
