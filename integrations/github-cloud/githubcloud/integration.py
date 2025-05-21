from typing import Any, Dict, List, AsyncGenerator

from port_ocean.core.integrations.base import BaseIntegration
from port_ocean.core.integrations.mixins.sync_raw import SyncRawMixin
from port_ocean.context.ocean import PortOceanContext
from port_ocean.core.handlers.webhook.webhook_event import WebhookEvent

from .clients.github_client import GitHubClient
from .fetchers.repository import RepositoryFetcher
from .fetchers.pull_request import PullRequestFetcher
from .fetchers.issue import IssueFetcher
from .fetchers.team import TeamFetcher
from .fetchers.workflow import WorkflowFetcher
from .webhooks.handler import GitHubWebhookHandler

class GitHubIntegration(
    BaseIntegration,
    SyncRawMixin,
):
    """GitHub Cloud integration for Port Ocean."""

    def __init__(self, context: PortOceanContext):
        super().__init__(context)
        self.github_client = None
        self.repository_fetcher = None
        self.pull_request_fetcher = None
        self.issue_fetcher = None
        self.team_fetcher = None
        self.workflow_fetcher = None
        self.webhook_handler = None

    async def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the integration."""
        token = context.get("token")
        if not token:
            raise ValueError("GitHub token is required")

        self.github_client = GitHubClient(token)
        self.repository_fetcher = RepositoryFetcher(self.github_client)
        self.pull_request_fetcher = PullRequestFetcher(self.github_client)
        self.issue_fetcher = IssueFetcher(self.github_client)
        self.team_fetcher = TeamFetcher(self.github_client)
        self.workflow_fetcher = WorkflowFetcher(self.github_client)
        self.webhook_handler = GitHubWebhookHandler(WebhookEvent(
            payload={},
            headers={"X-GitHub-Event": "push"},
            trace_id="test-trace-id"
        ))

    async def fetch_repositories(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch repositories."""
        org = context.get("org")
        result = self.repository_fetcher.fetch(org)
        return [item async for item in result]

    async def fetch_pull_requests(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch pull requests."""
        org = context.get("org")
        repo = context.get("repo")
        result = self.pull_request_fetcher.fetch(org, repo)
        return [item async for item in result]

    async def fetch_issues(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch issues."""
        org = context.get("org")
        repo = context.get("repo")
        result = self.issue_fetcher.fetch(org, repo)
        return [item async for item in result]

    async def fetch_teams(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch teams."""
        org = context.get("org")
        result = self.team_fetcher.fetch(org)
        return [item async for item in result]

    async def fetch_workflows(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch workflows."""
        org = context.get("org")
        repo = context.get("repo")
        result = self.workflow_fetcher.fetch(org, repo)
        return [item async for item in result]

    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, Any], resource_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle webhook events."""
        return await self.webhook_handler.handle_event(payload, resource_config)

    async def handle_resync(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle resync events."""
        # Fetch repositories
        repos = await self.fetch_repositories({"org": None})
        for repo in repos:
            yield {
                "kind": "repository",
                "identifier": repo["properties"]["name"],
                "title": repo["properties"]["name"],
                "properties": {
                    "description": repo.get("description"),
                    "language": repo["properties"]["language"],
                    "stars": repo["properties"]["stars"],
                    "forks": repo["properties"]["forks"],
                    "openIssues": repo["properties"]["openIssues"],
                    "createdAt": repo["properties"]["createdAt"],
                    "updatedAt": repo["properties"]["updatedAt"],
                    "pushedAt": repo["properties"]["pushedAt"],
                    "size": repo["properties"]["size"],
                    "visibility": repo["properties"]["visibility"],
                    "topics": repo["properties"].get("topics", []),
                    "owner": repo["relations"]["owner"]["title"]
                }
            }

            # Fetch pull requests for each repository
            prs = await self.fetch_pull_requests({"org": repo["relations"]["owner"]["title"], "repo": repo["properties"]["name"]})
            for pr in prs:
                yield {
                    "kind": "pull_request",
                    "identifier": str(pr["properties"]["number"]),
                    "title": pr["title"],
                    "properties": {
                        "number": pr["properties"]["number"],
                        "state": pr["properties"]["state"],
                        "createdAt": pr["properties"]["createdAt"],
                        "updatedAt": pr["properties"]["updatedAt"],
                        "additions": pr["properties"].get("additions", 0),
                        "deletions": pr["properties"].get("deletions", 0),
                        "author": pr["relations"]["author"]["title"],
                        "repository": repo["properties"]["name"]
                    }
                }

    async def handle_start_event(self) -> Dict[str, Any]:
        """Handle start events."""
        org = self.context.integration_config.get("org")
        if not org:
            raise ValueError("Organization name is required")

        response = await self.github_client._make_request("GET", f"/orgs/{org}")
        data = await response.json()

        return {
            "identifier": data["login"],
            "title": data["name"],
            "properties": {
                "description": data.get("description"),
                "createdAt": data.get("created_at"),
                "updatedAt": data.get("updated_at")
            }
        }

    async def register_webhook(self, repo: str, webhook_url: str, secret: str) -> Dict[str, Any]:
        """Register a webhook for a repository."""
        response = await self.github_client._make_request(
            "POST",
            f"/repos/{repo}/hooks",
            json={
                "name": "web",
                "active": True,
                "events": ["push", "pull_request"],
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "secret": secret
                }
            }
        )
        return await response.json()
