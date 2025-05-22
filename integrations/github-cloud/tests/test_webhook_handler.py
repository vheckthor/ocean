import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from port_ocean.core.handlers.webhook.webhook_event import WebhookEvent
from port_ocean.context.event import EventContext

from githubcloud.webhooks.handler import GitHubWebhookHandler

@pytest.fixture
def mock_event_context():
    with patch("port_ocean.context.event._event_context_stack") as mock_stack:
        mock_context = MagicMock(spec=EventContext)
        mock_context.attributes = {}
        mock_stack.top = mock_context
        yield mock_context

@pytest.fixture
def webhook_event():
    return WebhookEvent(
        payload={},
        headers={"X-GitHub-Event": "push"},
        trace_id="test-trace-id"
    )

@pytest.fixture
def webhook_handler(webhook_event):
    return GitHubWebhookHandler(event=webhook_event)

@pytest.mark.asyncio
async def test_should_process_event(webhook_handler):
    event = WebhookEvent(
        payload={},
        headers={"X-GitHub-Event": "push"},
        trace_id="test-trace-id"
    )
    assert await webhook_handler.should_process_event(event) is True

    event.headers = {"X-GitHub-Event": "invalid"}
    assert await webhook_handler.should_process_event(event) is False

@pytest.mark.asyncio
async def test_authenticate(webhook_handler):
    event = WebhookEvent(
        payload={},
        headers={
            "X-Hub-Signature": "sha1=valid_signature",
            "X-GitHub-Event": "push"
        },
        trace_id="test-trace-id"
    )
    with patch("githubcloud.webhooks.handler.hmac.new") as mock_hmac, \
         patch("port_ocean.context.ocean._port_ocean") as mock_ocean:
        mock_ocean.integration_config.get.return_value = "dummy_secret"
        mock_hmac.return_value.hexdigest.return_value = "valid_signature"
        assert await webhook_handler.authenticate(event.payload, event.headers) is True

    event.headers["X-Hub-Signature"] = "sha1=invalid_signature"
    with patch("port_ocean.context.ocean._port_ocean") as mock_ocean:
        mock_ocean.integration_config.get.return_value = "dummy_secret"
        assert await webhook_handler.authenticate(event.payload, event.headers) is False

@pytest.mark.asyncio
async def test_validate_payload(webhook_handler):
    event = WebhookEvent(
        payload={"repository": {}, "action": "opened", "pull_request": {}},
        headers={"X-GitHub-Event": "pull_request"},
        trace_id="test-trace-id"
    )
    assert await webhook_handler.validate_payload(event.payload) is True

    event.payload = {}
    assert await webhook_handler.validate_payload(event.payload) is False

@pytest.mark.asyncio
async def test_get_matching_kinds(webhook_handler):
    event = WebhookEvent(
        payload={},
        headers={"X-GitHub-Event": "push"},
        trace_id="test-trace-id"
    )
    kinds = await webhook_handler.get_matching_kinds(event)
    assert "repository" in kinds

    event.headers["X-GitHub-Event"] = "pull_request"
    kinds = await webhook_handler.get_matching_kinds(event)
    assert "pull-request" in kinds

    event.headers["X-GitHub-Event"] = "issues"
    kinds = await webhook_handler.get_matching_kinds(event)
    assert "issue" in kinds

    event.headers["X-GitHub-Event"] = "workflow_run"
    kinds = await webhook_handler.get_matching_kinds(event)
    assert "workflow" in kinds

@pytest.mark.asyncio
async def test_handle_event(webhook_handler):
    event = WebhookEvent(
        payload={
            "repository": {
                "id": 1,
                "name": "test-repo",
                "full_name": "test-org/test-repo",
                "private": False,
                "html_url": "https://github.com/test-org/test-repo",
                "description": "Test repository",
                "fork": False,
                "archived": False,
                "default_branch": "main",
                "language": "Python",
                "stargazers_count": 10,
                "forks_count": 5,
                "open_issues_count": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
                "pushed_at": "2024-01-02T00:00:00Z",
                "size": 100,
                "visibility": "public",
                "topics": ["test", "python"],
                "owner": {
                    "id": 1,
                    "login": "test-org"
                }
            },
            "headers": {"X-GitHub-Event": "push"}
        },
        headers={"X-GitHub-Event": "push"},
        trace_id="test-trace-id"
    )
    resource_config = {"token": "test-token"}
    result = await webhook_handler.handle_event(event.payload, resource_config)
    repo_entity = result.updated_raw_results[0]
    assert repo_entity["title"] == "test-repo"
    assert repo_entity["identifier"] == "1"

    event.headers["X-GitHub-Event"] = "pull_request"
    event.body = {
        "action": "opened",
        "pull_request": {
            "id": 1,
            "number": 1,
            "title": "Test PR",
            "body": "Test PR description",
            "html_url": "https://github.com/test-org/test-repo/pull/1",
            "state": "open",
            "locked": False,
            "draft": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "merge_commit_sha": None,
            "additions": 10,
            "deletions": 5,
            "changed_files": 2,
            "review_comments": 1,
            "comments": 2,
            "commits": 1,
            "base": {
                "repo": {
                    "id": 1,
                    "name": "test-repo"
                }
            },
            "user": {
                "id": 1,
                "login": "test-user"
            }
        },
        "repository": {},
        "headers": {"X-GitHub-Event": "pull_request"}
    }
    result = await webhook_handler.handle_event(event.body, resource_config)
    pr_entity = result.updated_raw_results[0]
    assert pr_entity["title"] == "Test PR"
    assert pr_entity["properties"]["number"] == 1

def test_handle_push_event(webhook_handler):
    payload = {
        "repository": {
            "id": 1,
            "name": "test-repo"
        },
        "head_commit": {
            "id": "abc123",
            "message": "Test commit",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "ref": "refs/heads/main",
        "pusher": {
            "name": "test-user"
        }
    }

    result = webhook_handler._handle_push_event(payload)
    entity = result.updated_raw_results[0]

    assert entity["kind"] == "repository"
    assert entity["identifier"] == "1"
    assert entity["title"] == "test-repo"
    assert entity["properties"]["lastCommit"] == "abc123"
    assert entity["properties"]["lastCommitMessage"] == "Test commit"
    assert entity["properties"]["branch"] == "main"
    assert entity["properties"]["pusher"] == "test-user"

def test_handle_pull_request_event(webhook_handler):
    payload = {
        "action": "opened",
        "pull_request": {
            "id": 1,
            "title": "Test PR",
            "state": "open",
            "number": 1,
            "updated_at": "2024-01-01T00:00:00Z",
            "user": {
                "login": "test-user"
            },
            "base": {
                "ref": "main"
            },
            "head": {
                "ref": "feature"
            },
            "mergeable": True,
            "mergeable_state": "clean"
        }
    }

    result = webhook_handler._handle_pull_request_event(payload)
    entity = result.updated_raw_results[0]

    assert entity["kind"] == "pull-request"
    assert entity["identifier"] == "1"
    assert entity["title"] == "Test PR"
    assert entity["properties"]["state"] == "open"
    assert entity["properties"]["action"] == "opened"
    assert entity["properties"]["number"] == 1
    assert entity["properties"]["author"] == "test-user"
    assert entity["properties"]["baseBranch"] == "main"
    assert entity["properties"]["headBranch"] == "feature"
    assert entity["properties"]["mergeable"] is True
    assert entity["properties"]["mergeableState"] == "clean"

def test_handle_issue_event(webhook_handler):
    payload = {
        "action": "opened",
        "issue": {
            "id": 1,
            "title": "Test Issue",
            "state": "open",
            "number": 1,
            "updated_at": "2024-01-01T00:00:00Z",
            "user": {
                "login": "test-user"
            },
            "assignees": [
                {"login": "assignee1"},
                {"login": "assignee2"}
            ],
            "labels": [
                {"name": "bug"},
                {"name": "enhancement"}
            ]
        }
    }

    result = webhook_handler._handle_issue_event(payload)
    entity = result.updated_raw_results[0]

    assert entity["kind"] == "issue"
    assert entity["identifier"] == "1"
    assert entity["title"] == "Test Issue"
    assert entity["properties"]["state"] == "open"
    assert entity["properties"]["action"] == "opened"
    assert entity["properties"]["number"] == 1
    assert entity["properties"]["author"] == "test-user"
    assert entity["properties"]["assignees"] == ["assignee1", "assignee2"]
    assert entity["properties"]["labels"] == ["bug", "enhancement"]

def test_handle_workflow_event(webhook_handler):
    payload = {
        "workflow_run": {
            "id": 1,
            "name": "Test Workflow",
            "status": "completed",
            "conclusion": "success",
            "updated_at": "2024-01-01T00:00:00Z",
            "triggering_actor": {
                "login": "test-user"
            },
            "head_branch": "main",
            "head_commit": {
                "id": "abc123"
            },
            "run_number": 1
        }
    }

    result = webhook_handler._handle_workflow_event(payload)
    entity = result.updated_raw_results[0]

    assert entity["kind"] == "workflow"
    assert entity["identifier"] == "1"
    assert entity["title"] == "Test Workflow"
    assert entity["properties"]["status"] == "completed"
    assert entity["properties"]["conclusion"] == "success"
    assert entity["properties"]["triggeredBy"] == "test-user"
    assert entity["properties"]["branch"] == "main"
    assert entity["properties"]["commit"] == "abc123"
    assert entity["properties"]["runNumber"] == 1
