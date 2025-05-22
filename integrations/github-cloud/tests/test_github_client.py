import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

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

@pytest.mark.asyncio
async def test_get_repositories(github_client, mock_http_client, mock_event_context):
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

    mock_http_client.request.return_value.json.return_value = mock_response

    repos = []
    async for repo in github_client.get_repositories():
        repos.append(repo)

    assert len(repos) == 1
    assert repos[0]["name"] == "test-repo"
    assert repos[0]["full_name"] == "test-org/test-repo"

    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"
    assert "/user/repos" in call_args[0][1]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"

@pytest.mark.asyncio
async def test_get_pull_requests(github_client, mock_http_client, mock_event_context):
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

    mock_http_client.request.return_value.json.return_value = mock_response

    prs = []
    async for pr in github_client.get_pull_requests("test-org", "test-repo"):
        prs.append(pr)

    assert len(prs) == 1
    assert prs[0]["title"] == "Test PR"
    assert prs[0]["number"] == 1

    mock_http_client.request.assert_called_once()
    call_args = mock_http_client.request.call_args
    assert call_args[0][0] == "GET"
    assert "/repos/test-org/test-repo/pulls" in call_args[0][1]
    assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
