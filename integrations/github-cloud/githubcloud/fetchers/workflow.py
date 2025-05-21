from typing import Any, AsyncGenerator, Dict
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)

class WorkflowFetcher(BaseFetcher):
    """Fetcher for GitHub Actions workflows."""

    async def fetch(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch workflows from GitHub."""
        try:
            async for workflow in self.client.get_workflows(owner, repo):
                yield self.transform(workflow)
        except Exception as e:
            logger.error(f"Error fetching workflows: {str(e)}")
            raise

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw workflow data into Port-compatible format."""
        return {
            "identifier": str(raw_data["id"]),
            "title": raw_data["name"],
            "description": raw_data.get("description", ""),
            "url": raw_data["html_url"],
            "properties": {
                "name": raw_data["name"],
                "path": raw_data["path"],
                "state": raw_data["state"],
                "createdAt": raw_data["created_at"],
                "updatedAt": raw_data["updated_at"],
                "badgeUrl": raw_data.get("badge_url"),
                "nodeId": raw_data["node_id"],
            },
            "relations": {
                "repository": {
                    "identifier": str(raw_data["repository"]["id"]),
                    "title": raw_data["repository"]["name"],
                }
            }
        }
