from typing import Any, AsyncGenerator, Dict
import logging

from .base import BaseFetcher

logger = logging.getLogger(__name__)

class PullRequestFetcher(BaseFetcher):
    """Fetcher for GitHub pull requests."""

    async def fetch(self, owner: str, repo: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch pull requests from GitHub."""
        try:
            async for pr in self.client.get_pull_requests(owner, repo):
                yield self.transform(pr)
        except Exception as e:
            logger.error(f"Error fetching pull requests: {str(e)}")
            raise

    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw pull request data into Port-compatible format."""
        return {
            "identifier": str(raw_data["id"]),
            "title": raw_data["title"],
            "description": raw_data.get("body", ""),
            "url": raw_data["html_url"],
            "properties": {
                "number": raw_data["number"],
                "state": raw_data["state"],
                "locked": raw_data["locked"],
                "draft": raw_data["draft"],
                "createdAt": raw_data["created_at"],
                "updatedAt": raw_data["updated_at"],
                "closedAt": raw_data.get("closed_at"),
                "mergedAt": raw_data.get("merged_at"),
                "mergeCommitSha": raw_data.get("merge_commit_sha"),
                "additions": raw_data["additions"],
                "deletions": raw_data["deletions"],
                "changedFiles": raw_data["changed_files"],
                "reviewComments": raw_data["review_comments"],
                "comments": raw_data["comments"],
                "commits": raw_data["commits"],
            },
            "relations": {
                "repository": {
                    "identifier": str(raw_data["base"]["repo"]["id"]),
                    "title": raw_data["base"]["repo"]["name"],
                },
                "author": {
                    "identifier": str(raw_data["user"]["id"]),
                    "title": raw_data["user"]["login"],
                }
            }
        }
