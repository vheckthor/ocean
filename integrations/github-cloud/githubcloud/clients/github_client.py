from typing import Any, AsyncGenerator, Dict, Optional
import logging
import aiolimiter
from port_ocean.utils.async_http import http_async_client
from port_ocean.utils.cache import cache_iterator_result
from ..errors import GitHubRateLimitError, GitHubAuthenticationError

logger = logging.getLogger(__name__)

class GitHubClient:
    """Async client for interacting with GitHub's API with rate limiting and pagination support."""

    BASE_URL = "https://api.github.com"
    RATE_LIMIT_PER_HOUR = 5000

    def __init__(self, token: str, http_client=None):
        self.token = token
        self.http_client = http_client or http_async_client
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self._rate_limiter = aiolimiter.AsyncLimiter(self.RATE_LIMIT_PER_HOUR * 0.95, 3600)

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a rate-limited request to GitHub API."""
        async with self._rate_limiter:
            try:
                response = await self.http_client.request(
                    method,
                    f"{self.BASE_URL}{endpoint}",
                    headers=self.headers,
                    **kwargs
                )

                # Check rate limit headers
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                if remaining < 100:  # Warning threshold
                    logger.warning(f"GitHub API rate limit running low: {remaining} requests remaining")

                if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                    raise GitHubRateLimitError("GitHub API rate limit exceeded")
                elif response.status_code == 401:
                    raise GitHubAuthenticationError("GitHub authentication failed")

                return response

            except Exception as e:
                logger.error(f"Error making request to {endpoint}: {str(e)}")
                raise

    @cache_iterator_result()
    async def _paginated_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Make paginated requests to GitHub API with rate limit handling."""
        page = 1
        per_page = 100

        while True:
            try:
                params = params or {}
                params.update({"page": page, "per_page": per_page})

                response = await self._make_request("GET", endpoint, params=params)
                data = await response.json()

                if not data:
                    break

                for item in data:
                    yield item

                if len(data) < per_page:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error fetching data from {endpoint}: {str(e)}")
                raise

    async def get_repositories(self, org: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch repositories for an organization or user."""
        endpoint = f"/orgs/{org}/repos" if org else "/user/repos"
        async for repo in self._paginated_request(endpoint):
            yield repo

    async def get_pull_requests(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch pull requests for a repository."""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        async for pr in self._paginated_request(endpoint):
            yield pr

    async def get_issues(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch issues for a repository."""
        endpoint = f"/repos/{owner}/{repo}/issues"
        async for issue in self._paginated_request(endpoint):
            yield issue

    async def get_teams(self, org: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch teams for an organization."""
        endpoint = f"/orgs/{org}/teams"
        async for team in self._paginated_request(endpoint):
            yield team

    async def get_workflows(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch GitHub Actions workflows for a repository."""
        endpoint = f"/repos/{owner}/{repo}/actions/workflows"
        async for workflow in self._paginated_request(endpoint):
            yield workflow
