from typing import Any, AsyncGenerator, Dict
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)

class TeamFetcher(BaseFetcher):
    """Fetcher for GitHub teams."""

    async def fetch(self, org: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch teams from GitHub."""
        try:
            async for team in self.client.get_teams(org):
                yield self.transform(team)
        except Exception as e:
            logger.error(f"Error fetching teams: {str(e)}")
            raise

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw team data into Port-compatible format."""
        return {
            "identifier": str(raw_data["id"]),
            "title": raw_data["name"],
            "description": raw_data.get("description", ""),
            "url": raw_data["html_url"],
            "properties": {
                "name": raw_data["name"],
                "slug": raw_data["slug"],
                "privacy": raw_data["privacy"],
                "permission": raw_data["permission"],
                "membersCount": raw_data["members_count"],
                "reposCount": raw_data["repos_count"],
                "createdAt": raw_data["created_at"],
                "updatedAt": raw_data["updated_at"],
            },
            "relations": {
                "organization": {
                    "identifier": str(raw_data["organization"]["id"]),
                    "title": raw_data["organization"]["login"],
                }
            }
        }
