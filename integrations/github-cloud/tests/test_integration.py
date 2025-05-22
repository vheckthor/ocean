import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.context.event import EventContext

from githubcloud.integration import GitHubIntegration
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
async def integration(mock_ocean_context, mock_http_client):
    """Create and initialize the GitHub integration."""
    integration = GitHubIntegration(mock_ocean_context)
    await integration.initialize({"token": "test-token", "org": "test-org"})

    integration.github_client.http_client = mock_http_client
    mock_ocean_context._integration = integration
    yield integration

@pytest.mark.asyncio
async def test_initialize(integration):
    """Test initialization with valid token."""
    await integration.initialize({"token": "test-token"})
    assert integration.github_client is not None
    assert integration.repository_fetcher is not None
    assert integration.pull_request_fetcher is not None
    assert integration.issue_fetcher is not None
    assert integration.team_fetcher is not None
    assert integration.workflow_fetcher is not None
    assert integration.webhook_handler is not None

@pytest.mark.asyncio
async def test_initialize_missing_token():
    """Test initialization fails without token."""
    integration = GitHubIntegration(MagicMock())
    with pytest.raises(ValueError, match="GitHub token is required"):
        await integration.initialize({})

@pytest.mark.asyncio
async def test_handle_resync(integration, mock_http_client, mock_event_context):
    """Test resync event handling."""
    mock_repos_response = [
        {
            "id": 1,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "description": "Test repository",
            "language": "Python",
            "html_url": "https://github.com/test-org/test-repo",
            "private": False,
            "fork": False,
            "archived": False,
            "default_branch": "main",
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

    mock_prs_response = [
        {
            "id": 1,
            "number": 1,
            "title": "Test PR",
            "body": "Test PR description",
            "html_url": "https://github.com/test-org/test-repo/pull/1",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "additions": 100,
            "deletions": 50,
            "locked": False,
            "draft": False,
            "changed_files": 3,
            "review_comments": 2,
            "comments": 5,
            "commits": 3,
            "user": {
                "id": 1,
                "login": "test-user"
            },
            "base": {
                "repo": {
                    "id": 1,
                    "name": "test-repo"
                }
            }
        }
    ]

    mock_http_client.request.return_value.json.side_effect = [
        mock_repos_response,
        mock_prs_response,
        []
    ]

    entities = [entity async for entity in integration.handle_resync()]

    assert len(entities) == 2

    repo_entity = next(e for e in entities if e["kind"] == "repository")
    assert repo_entity["identifier"] == "test-repo"
    assert repo_entity["title"] == "test-repo"
    assert repo_entity["properties"]["description"] == "Test repository"
    assert repo_entity["properties"]["language"] == "Python"

    pr_entity = next(e for e in entities if e["kind"] == "pull_request")
    assert pr_entity["identifier"] == "1"
    assert pr_entity["title"] == "Test PR"
    assert pr_entity["properties"]["number"] == 1
    assert pr_entity["properties"]["state"] == "open"

@pytest.mark.asyncio
async def test_handle_start_event(integration, mock_http_client, mock_event_context):
    """Test start event handling."""
    mock_response = {
        "id": 1,
        "name": "test-org",
        "login": "test-org",
        "description": "Test organization",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z"
    }

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.handle_start_event()

    assert result["identifier"] == "test-org"
    assert result["title"] == "test-org"
    assert result["properties"]["description"] == "Test organization"
    assert result["properties"]["createdAt"] == "2024-01-01T00:00:00Z"
    assert result["properties"]["updatedAt"] == "2024-01-02T00:00:00Z"

@pytest.mark.asyncio
async def test_register_webhook(integration, mock_http_client, mock_event_context):
    """Test webhook registration."""
    mock_response = {
        "id": 1,
        "url": "https://api.github.com/repos/test-org/test-repo/hooks/1",
        "name": "web",
        "active": True,
        "events": ["push", "pull_request"],
        "config": {
            "url": "https://example.com/webhook",
            "content_type": "json",
            "secret": "test-secret"
        }
    }

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.register_webhook("test-org/test-repo", "https://example.com/webhook", "test-secret")

    assert result["id"] == 1
    assert result["url"] == "https://api.github.com/repos/test-org/test-repo/hooks/1"
    assert result["active"] is True
    assert "push" in result["events"]
    assert "pull_request" in result["events"]
    assert result["config"]["url"] == "https://example.com/webhook"
    assert result["config"]["content_type"] == "json"
    assert result["config"]["secret"] == "test-secret"

@pytest.mark.asyncio
async def test_fetch_repositories(integration, mock_http_client, mock_event_context):
    """Test repository fetching."""
    mock_response = [
        {
            "id": 1,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "description": "Test repository",
            "language": "Python",
            "html_url": "https://github.com/test-org/test-repo",
            "private": False,
            "fork": False,
            "archived": False,
            "default_branch": "main",
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

    result = await integration.fetch_repositories({"org": "test-org"})

    assert len(result) == 1
    assert result[0]["properties"]["name"] == "test-repo"
    assert result[0]["properties"]["fullName"] == "test-org/test-repo"
    assert result[0]["description"] == "Test repository"
    assert result[0]["properties"]["language"] == "Python"

@pytest.mark.asyncio
async def test_fetch_pull_requests(integration, mock_http_client, mock_event_context):
    """Test pull request fetching."""
    mock_response = [
        {
            "id": 1,
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "html_url": "https://github.com/test-org/test-repo/pull/1",
            "body": "Test PR body",
            "locked": False,
            "draft": False,
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "additions": 10,
            "deletions": 2,
            "changed_files": 1,
            "review_comments": 0,
            "comments": 0,
            "commits": 1,
            "base": {"repo": {"id": 1, "name": "test-repo"}},
            "user": {"id": 2, "login": "test-user"}
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.fetch_pull_requests({"org": "test-org", "repo": "test-repo"})

    assert len(result) == 1
    assert result[0]["properties"]["number"] == 1
    assert result[0]["title"] == "Test PR"
    assert result[0]["properties"]["state"] == "open"

@pytest.mark.asyncio
async def test_fetch_issues(integration, mock_http_client, mock_event_context):
    """Test issue fetching."""
    mock_response = [
        {
            "id": 1,
            "number": 1,
            "title": "Test Issue",
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "html_url": "https://github.com/test-org/test-repo/issues/1",
            "body": "Test issue body",
            "locked": False,
            "closed_at": None,
            "comments": 0,
            "labels": [],
            "assignees": [],
            "milestone": None,
            "repository": {"id": 1, "name": "test-repo"},
            "user": {"id": 2, "login": "test-user"}
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.fetch_issues({"org": "test-org", "repo": "test-repo"})

    assert len(result) == 1
    assert result[0]["properties"]["number"] == 1
    assert result[0]["title"] == "Test Issue"
    assert result[0]["properties"]["state"] == "open"

@pytest.mark.asyncio
async def test_fetch_teams(integration, mock_http_client, mock_event_context):
    """Test team fetching."""
    mock_response = [
        {
            "id": 1,
            "name": "Test Team",
            "slug": "test-team",
            "description": "Test team description",
            "html_url": "https://github.com/orgs/test-org/teams/test-team",
            "privacy": "closed",
            "permission": "admin",
            "members_count": 5,
            "repos_count": 2,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "organization": {"id": 1, "login": "test-org"}
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.fetch_teams({"org": "test-org"})

    assert len(result) == 1
    assert result[0]["properties"]["name"] == "Test Team"
    assert result[0]["properties"]["slug"] == "test-team"
    assert result[0]["description"] == "Test team description"

@pytest.mark.asyncio
async def test_fetch_workflows(integration, mock_http_client, mock_event_context):
    """Test workflow fetching."""
    mock_response = [
        {
            "id": 1,
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": "active",
            "html_url": "https://github.com/test-org/test-repo/actions/workflows/1",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "badge_url": "https://github.com/test-org/test-repo/workflows/test/badge.svg",
            "node_id": "MDg6V29ya2Zsb3cx",
            "repository": {"id": 1, "name": "test-repo"}
        }
    ]

    mock_http_client.request.return_value.json.return_value = mock_response

    result = await integration.fetch_workflows({"org": "test-org", "repo": "test-repo"})

    assert len(result) == 1
    assert result[0]["properties"]["name"] == "Test Workflow"
    assert result[0]["properties"]["path"] == ".github/workflows/test.yml"
    assert result[0]["properties"]["state"] == "active"
