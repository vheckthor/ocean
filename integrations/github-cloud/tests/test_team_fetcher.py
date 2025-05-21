import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.fetchers.team import TeamFetcher
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
def team_fetcher(github_client):
    return TeamFetcher(github_client)

@pytest.mark.asyncio
async def test_fetch_teams(team_fetcher, mock_http_client, mock_event_context):
    # Test data
    mock_response = [
        {
            "id": 1,
            "name": "test-team",
            "slug": "test-team",
            "description": "Test team description",
            "privacy": "closed",
            "permission": "push",
            "members_count": 5,
            "repos_count": 10,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "html_url": "https://github.com/orgs/test-org/teams/test-team",
            "organization": {
                "id": 1,
                "login": "test-org"
            },
            "parent": None
        }
    ]

    # Mock the HTTP response
    mock_http_client.request.return_value.json.return_value = mock_response

    # Test the method
    entities = []
    async for entity in team_fetcher.fetch("test-org"):
        entities.append(entity)

    assert len(entities) == 1
    assert entities[0]["identifier"] == "1"
    assert entities[0]["title"] == "test-team"
    assert entities[0]["url"] == "https://github.com/orgs/test-org/teams/test-team"
    assert entities[0]["properties"]["slug"] == "test-team"
    assert entities[0]["properties"]["privacy"] == "closed"
    assert entities[0]["properties"]["permission"] == "push"
    assert entities[0]["properties"]["membersCount"] == 5
    assert entities[0]["properties"]["reposCount"] == 10
    assert entities[0]["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert entities[0]["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"
    assert entities[0]["relations"]["organization"]["title"] == "test-org"
    assert entities[0]["relations"]["organization"]["identifier"] == "1"

    # Verify the HTTP client was called correctly
    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"  # First positional arg is method
    assert "/orgs/test-org/teams" in call_args[0][1]  # Second positional arg is URL
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
