import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.fetchers.pull_request import PullRequestFetcher
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
    mock_response.json = AsyncMock(return_value=[])  # Default empty response
    client.request.return_value = mock_response
    return client

@pytest.fixture
def github_client(mock_http_client):
    return GitHubClient("test-token", mock_http_client)

@pytest.fixture
def pull_request_fetcher(github_client):
    return PullRequestFetcher(github_client)

@pytest.mark.asyncio
async def test_fetch_pull_requests(pull_request_fetcher, mock_http_client, mock_event_context):
    # Test data
    mock_response = [
        {
            "id": 1,
            "number": 1,
            "title": "Test PR",
            "body": "Test PR description",
            "html_url": "https://github.com/test-org/test-repo/pull/1",
            "state": "open",
            "locked": False,
            "draft": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "additions": 10,
            "deletions": 5,
            "changed_files": 2,
            "review_comments": 1,
            "comments": 2,
            "commits": 1,
            "base": {
                "repo": {
                    "id": 1,
                    "name": "test-repo"
                }
            },
            "user": {
                "id": 1,
                "login": "test-user"
            }
        }
    ]

    # Mock the HTTP response
    mock_http_client.request.return_value.json.return_value = mock_response

    # Test the method
    entities = []
    async for entity in pull_request_fetcher.fetch("test-org", "test-repo"):
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0]["identifier"] == "1"
    assert entities[0]["title"] == "Test PR"
    assert entities[0]["url"] == "https://github.com/test-org/test-repo/pull/1"
    assert entities[0]["properties"]["number"] == 1
    assert entities[0]["properties"]["state"] == "open"
    assert entities[0]["properties"]["draft"] is False
    assert entities[0]["properties"]["locked"] is False
    assert entities[0]["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert entities[0]["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["properties"]["closedAt"] is None
    assert entities[0]["properties"]["mergedAt"] is None
    assert entities[0]["properties"]["additions"] == 10
    assert entities[0]["properties"]["deletions"] == 5
    assert entities[0]["properties"]["changedFiles"] == 2
    assert entities[0]["properties"]["reviewComments"] == 1
    assert entities[0]["properties"]["comments"] == 2
    assert entities[0]["properties"]["commits"] == 1
    assert entities[0]["relations"]["author"]["title"] == "test-user"
    assert entities[0]["relations"]["repository"]["title"] == "test-repo"

    # Verify the HTTP client was called correctly
    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"  # First positional arg is method
    assert "/repos/test-org/test-repo/pulls" in call_args[0][1]  # Second positional arg is URL
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
