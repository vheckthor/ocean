from typing import Any, Dict, List
import logging
import asyncio

from port_ocean.context.ocean import ocean
from port_ocean.core.handlers.port_app_config.models import PortAppConfig
from port_ocean.core.integrations.base import BaseIntegration
from .webhooks.handler import GitHubWebhookHandler

from .clients.github_client import GitHubClient
from .fetchers.repository import RepositoryFetcher
from .fetchers.pull_request import PullRequestFetcher
from .fetchers.issue import IssueFetcher
from .fetchers.team import TeamFetcher
from .fetchers.workflow import WorkflowFetcher

logger = logging.getLogger(__name__)

# Initialize fetchers
fetchers = {}

class GitHubIntegration(BaseIntegration):
    """GitHub Cloud integration for Port Ocean."""

    def __init__(self, context):
        super().__init__(context)
        # Register webhook processor
        ocean.add_webhook_processor("/webhook", GitHubWebhookHandler)

@ocean.on_start()
async def on_start(port_app_config: PortAppConfig) -> None:
    """Initialize the integration when it starts."""
    try:
        # Get GitHub token from configuration
        token = port_app_config.integration.config.get("token")
        if not token:
            raise ValueError("GitHub token not configured")

        # Initialize GitHub client
        client = GitHubClient(token, ocean.http_client)

        # Initialize fetchers
        global fetchers
        fetchers = {
            "repository": RepositoryFetcher(client),
            "pull-request": PullRequestFetcher(client),
            "issue": IssueFetcher(client),
            "team": TeamFetcher(client),
            "workflow": WorkflowFetcher(client),
        }

        logger.info("GitHub integration initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing GitHub integration: {str(e)}")
        raise

@ocean.on_resync()
async def on_resync(kind: str) -> List[Dict[str, Any]]:
    """Handle resync events for different entity kinds."""
    try:
        if kind not in fetchers:
            logger.warning(f"Unhandled kind: {kind}")
            return []

        fetcher = fetchers[kind]
        entities = []

        # Get organization from configuration
        org = ocean.port_app_config.integration.config.get("organization")

        if kind == "repository":
            async for entity in fetcher.fetch(org):
                entities.append(entity)
        elif kind == "team":
            if not org:
                logger.error("Organization not configured for team fetching")
                return []
            async for entity in fetcher.fetch(org):
                entities.append(entity)
        else:
            # For repository-specific entities, we need to fetch repositories first
            repo_fetcher = fetchers["repository"]
            async for repo in repo_fetcher.fetch(org):
                owner = repo["properties"]["fullName"].split("/")[0]
                repo_name = repo["properties"]["fullName"].split("/")[1]

                async for entity in fetcher.fetch(owner, repo_name):
                    entities.append(entity)

        return entities

    except Exception as e:
        logger.error(f"Error during resync for kind {kind}: {str(e)}")
        raise


# The same sync logic can be registered for one of the kinds that are available in the mapping in port.
# @ocean.on_resync('project')
# async def resync_project(kind: str) -> list[dict[Any, Any]]:
#     # 1. Get all projects from the source system
#     # 2. Return a list of dictionaries with the raw data of the state
#     return [{"some_project_key": "someProjectValue", ...}]
#
# @ocean.on_resync('issues')
# async def resync_issues(kind: str) -> list[dict[Any, Any]]:
#     # 1. Get all issues from the source system
#     # 2. Return a list of dictionaries with the raw data of the state
#     return [{"some_issue_key": "someIssueValue", ...}]


# Optional
# Listen to the start event of the integration. Called once when the integration starts.
@ocean.on_start()
async def on_start() -> None:
    # Something to do when the integration starts
    # For example create a client to query 3rd party services - GitHub, Jira, etc...
    print("Starting githubcloud integration")
