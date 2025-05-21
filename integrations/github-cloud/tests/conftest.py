from typing import Any
from unittest.mock import AsyncMock
import pytest

from githubcloud.clients.github_client import GitHubClient
from githubcloud.webhooks.handler import GitHubWebhookHandler

@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Mock HTTP client for testing."""
    return AsyncMock()

@pytest.fixture
def github_client(mock_http_client: AsyncMock) -> GitHubClient:
    """GitHub client fixture with mocked HTTP client."""
    return GitHubClient("test-token", mock_http_client)

@pytest.fixture
def webhook_handler() -> GitHubWebhookHandler:
    """Webhook handler fixture with test secret."""
    return GitHubWebhookHandler("test-secret")

@pytest.fixture
def mock_webhook_payload() -> dict[str, Any]:
    """Sample webhook payload for testing."""
    return {
        "repository": {
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
    }
