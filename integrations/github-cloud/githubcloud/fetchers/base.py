from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from ..clients.github_client import GitHubClient

class BaseFetcher(ABC):
    """Base class for all GitHub entity fetchers."""

    def __init__(self, client: GitHubClient):
        self.client = client

    @abstractmethod
    async def fetch(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch entities from GitHub and yield them one by one."""
        pass

    @abstractmethod
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw GitHub data into Port-compatible entity format."""
        pass
