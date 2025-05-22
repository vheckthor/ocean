from typing import Any, AsyncGenerator, Dict
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)

class IssueFetcher(BaseFetcher):
    """Fetcher for GitHub issues."""

    async def fetch(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch issues from GitHub."""
        try:
            async for issue in self.client.get_issues(owner, repo):
                if "pull_request" in issue:
                    continue
                yield self.transform(issue)
        except Exception as e:
            logger.error(f"Error fetching issues: {str(e)}")
            raise

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw issue data into Port-compatible format."""
        return {
            "identifier": str(raw_data["id"]),
            "title": raw_data["title"],
            "description": raw_data.get("body", ""),
            "url": raw_data["html_url"],
            "properties": {
                "number": raw_data["number"],
                "state": raw_data["state"],
                "locked": raw_data["locked"],
                "createdAt": raw_data["created_at"],
                "updatedAt": raw_data["updated_at"],
                "closedAt": raw_data.get("closed_at"),
                "comments": raw_data["comments"],
                "labels": [label["name"] for label in raw_data["labels"]],
                "assignees": [assignee["login"] for assignee in raw_data["assignees"]],
                "milestone": raw_data.get("milestone", {}).get("title") if raw_data.get("milestone") else None,
            },
            "relations": {
                "repository": {
                    "identifier": str(raw_data["repository"]["id"]),
                    "title": raw_data["repository"]["name"],
                },
                "author": {
                    "identifier": str(raw_data["user"]["id"]),
                    "title": raw_data["user"]["login"],
                }
            }
        }
