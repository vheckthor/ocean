from typing import Any, AsyncGenerator, Dict, Optional
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)

class RepositoryFetcher(BaseFetcher):
    """Fetcher for GitHub repositories."""

    async def fetch(self, org: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch repositories from GitHub."""
        try:
            async for repo in self.client.get_repositories(org):
                yield self.transform(repo)
        except Exception as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            raise

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw repository data into Port-compatible format."""
        return {
            "identifier": str(raw_data["id"]),
            "title": raw_data["name"],
            "description": raw_data.get("description", ""),
            "url": raw_data["html_url"],
            "properties": {
                "name": raw_data["name"],
                "fullName": raw_data["full_name"],
                "private": raw_data["private"],
                "fork": raw_data["fork"],
                "archived": raw_data["archived"],
                "defaultBranch": raw_data["default_branch"],
                "language": raw_data.get("language"),
                "stars": raw_data["stargazers_count"],
                "forks": raw_data["forks_count"],
                "openIssues": raw_data["open_issues_count"],
                "createdAt": raw_data["created_at"],
                "updatedAt": raw_data["updated_at"],
                "pushedAt": raw_data["pushed_at"],
                "size": raw_data["size"],
                "visibility": raw_data["visibility"],
                "topics": raw_data.get("topics", []),
            },
            "relations": {
                "owner": {
                    "identifier": str(raw_data["owner"]["id"]),
                    "title": raw_data["owner"]["login"],
                }
            }
        }
