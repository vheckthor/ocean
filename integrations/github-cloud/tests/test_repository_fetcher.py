import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.fetchers.repository import RepositoryFetcher
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
def repository_fetcher(github_client):
    return RepositoryFetcher(github_client)

@pytest.mark.asyncio
async def test_fetch_repositories(repository_fetcher, mock_http_client, mock_event_context):
    # Test data
    mock_response = [
        {
            "id": 1,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "private": False,
            "html_url": "https://github.com/test-org/test-repo",
            "description": "Test repository",
            "fork": False,
            "archived": False,
            "default_branch": "main",
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 5,
            "open_issues_count": 2,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "pushed_at": "2024-01-02T00:00:00Z",
            "size": 100,
            "visibility": "public",
            "topics": ["test", "python"],
            "owner": {
                "id": 1,
                "login": "test-org"
            }
        }
    ]

    # Mock the HTTP response
    mock_http_client.request.return_value.json.return_value = mock_response

    # Test the method
    entities = []
    async for entity in repository_fetcher.fetch("test-org"):
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0]["identifier"] == "1"
    assert entities[0]["title"] == "test-repo"
    assert entities[0]["url"] == "https://github.com/test-org/test-repo"
    assert entities[0]["properties"]["fullName"] == "test-org/test-repo"
    assert entities[0]["properties"]["private"] is False
    assert entities[0]["properties"]["fork"] is False
    assert entities[0]["properties"]["archived"] is False
    assert entities[0]["properties"]["defaultBranch"] == "main"
    assert entities[0]["properties"]["language"] == "Python"
    assert entities[0]["properties"]["stars"] == 10
    assert entities[0]["properties"]["forks"] == 5
    assert entities[0]["properties"]["openIssues"] == 2
    assert entities[0]["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert entities[0]["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["properties"]["pushedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["properties"]["size"] == 100
    assert entities[0]["properties"]["visibility"] == "public"
    assert entities[0]["properties"]["topics"] == ["test", "python"]
    assert entities[0]["relations"]["owner"]["title"] == "test-org"

    # Verify the HTTP client was called correctly
    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"  # First positional arg is method
    assert "/orgs/test-org/repos" in call_args[0][1]  # Second positional arg is URL
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
