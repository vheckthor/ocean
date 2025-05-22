import hmac
import hashlib
import json
import logging
from typing import Any, Dict, List
from port_ocean.context.ocean import ocean
from port_ocean.core.handlers.webhook.abstract_webhook_processor import AbstractWebhookProcessor
from port_ocean.core.handlers.webhook.webhook_event import EventPayload, WebhookEvent, WebhookEventRawResults
from port_ocean.core.handlers.port_app_config.models import ResourceConfig

logger = logging.getLogger(__name__)

class GitHubWebhookHandler(AbstractWebhookProcessor):
    """Processor for GitHub webhook events."""

    SUPPORTED_EVENTS = [
        "push",
        "pull_request",
        "issues",
        "workflow_run",
        "create",
        "delete",
        "fork",
        "star",
        "watch",
        "release"
    ]

    async def should_process_event(self, event: WebhookEvent) -> bool:
        """Determine if the event should be processed."""
        event_type = event.headers.get("X-GitHub-Event")
        return event_type in self.SUPPORTED_EVENTS

    async def authenticate(self, payload: EventPayload, headers: Dict[str, Any]) -> bool:
        """Verify the GitHub webhook signature."""
        signature = headers.get("X-Hub-Signature")
        if not signature or not signature.startswith("sha1="):
            logger.error("Invalid signature format")
            return False

        try:
            webhook_secret = ocean.integration_config.get("webhook_secret")
            if not webhook_secret:
                logger.error("Webhook secret not configured")
                return False

            expected = hmac.new(
                webhook_secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha1
            ).hexdigest()

            return hmac.compare_digest(f"sha1={expected}", signature)
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False

    async def validate_payload(self, payload: EventPayload) -> bool:
        """Validate the webhook payload."""
        return "repository" in payload

    async def get_matching_kinds(self, event: WebhookEvent) -> List[str]:
        """Get the matching kinds for the event."""
        event_type = event.headers.get("X-GitHub-Event")
        if event_type == "push":
            return ["repository"]
        elif event_type == "pull_request":
            return ["pull-request"]
        elif event_type == "issues":
            return ["issue"]
        elif event_type == "workflow_run":
            return ["workflow"]
        return []

    async def handle_event(
        self, payload: EventPayload, resource_config: ResourceConfig
    ) -> WebhookEventRawResults:
        """Handle the webhook event."""
        event_type = payload.get("headers", {}).get("X-GitHub-Event")

        if event_type == "push":
            return self._handle_push_event(payload)
        elif event_type == "pull_request":
            return self._handle_pull_request_event(payload)
        elif event_type == "issues":
            return self._handle_issue_event(payload)
        elif event_type == "workflow_run":
            return self._handle_workflow_event(payload)

        return WebhookEventRawResults(updated_raw_results=[], deleted_raw_results=[])

    def _handle_push_event(self, payload: EventPayload) -> WebhookEventRawResults:
        """Handle push events."""
        repo = payload.get("repository", {})
        commit = payload.get("head_commit", {})

        entity = {
            "kind": "repository",
            "identifier": str(repo.get("id")),
            "title": repo.get("name"),
            "properties": {
                "lastCommit": commit.get("id"),
                "lastCommitMessage": commit.get("message"),
                "branch": payload.get("ref", "").replace("refs/heads/", ""),
                "pusher": payload.get("pusher", {}).get("name")
            }
        }

        return WebhookEventRawResults(updated_raw_results=[entity], deleted_raw_results=[])

    def _handle_pull_request_event(self, payload: EventPayload) -> WebhookEventRawResults:
        """Handle pull request events."""
        pr = payload.get("pull_request", {})

        entity = {
            "kind": "pull-request",
            "identifier": str(pr.get("id")),
            "title": pr.get("title"),
            "properties": {
                "state": pr.get("state"),
                "action": payload.get("action"),
                "number": pr.get("number"),
                "author": pr.get("user", {}).get("login"),
                "baseBranch": pr.get("base", {}).get("ref"),
                "headBranch": pr.get("head", {}).get("ref"),
                "mergeable": pr.get("mergeable"),
                "mergeableState": pr.get("mergeable_state")
            }
        }

        return WebhookEventRawResults(updated_raw_results=[entity], deleted_raw_results=[])

    def _handle_issue_event(self, payload: EventPayload) -> WebhookEventRawResults:
        """Handle issue events."""
        issue = payload.get("issue", {})

        entity = {
            "kind": "issue",
            "identifier": str(issue.get("id")),
            "title": issue.get("title"),
            "properties": {
                "state": issue.get("state"),
                "action": payload.get("action"),
                "number": issue.get("number"),
                "author": issue.get("user", {}).get("login"),
                "assignees": [a.get("login") for a in issue.get("assignees", [])],
                "labels": [l.get("name") for l in issue.get("labels", [])]
            }
        }

        return WebhookEventRawResults(updated_raw_results=[entity], deleted_raw_results=[])

    def _handle_workflow_event(self, payload: EventPayload) -> WebhookEventRawResults:
        """Handle workflow events."""
        workflow = payload.get("workflow_run", {})

        entity = {
            "kind": "workflow",
            "identifier": str(workflow.get("id")),
            "title": workflow.get("name"),
            "properties": {
                "status": workflow.get("status"),
                "conclusion": workflow.get("conclusion"),
                "triggeredBy": workflow.get("triggering_actor", {}).get("login"),
                "branch": workflow.get("head_branch"),
                "commit": workflow.get("head_commit", {}).get("id"),
                "runNumber": workflow.get("run_number")
            }
        }

        return WebhookEventRawResults(updated_raw_results=[entity], deleted_raw_results=[])
