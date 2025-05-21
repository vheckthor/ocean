# GitHub Cloud Integration for Port

This integration connects Port with GitHub Cloud, allowing you to sync repositories, pull requests, issues, teams, and workflows into your Port catalog.

## Features

- Sync GitHub repositories, including metadata and relationships
- Track pull requests and their status
- Monitor issues and their assignments
- Manage teams and their memberships
- Track GitHub Actions workflows
- Real-time updates via webhooks
- Rate limit handling and pagination support
- Pure async implementation using Ocean's HTTP client

## Prerequisites

- Python 3.12 or higher
- A GitHub account with appropriate permissions
- A Port account with admin access

## Installation

1. Install the integration using Helm:

```bash
helm repo add port-labs https://port-labs.github.io/helm-charts
helm install github-cloud port-labs/ocean --namespace port-ocean --create-namespace
```

2. Configure the integration with your GitHub token and organization:

```yaml
# values.yaml
integration:
  config:
    token: "your-github-token"
    organization: "your-org-name"  # Optional, for organization-wide sync
    webhook_secret: "your-webhook-secret"  # Optional, for webhook support
```

## Configuration

### Required Configuration

- `token`: Your GitHub personal access token with appropriate permissions:
  - `repo` scope for repository access
  - `read:org` scope for team access
  - `workflow` scope for GitHub Actions access

### Optional Configuration

- `organization`: Your GitHub organization name for organization-wide sync
- `webhook_secret`: Secret for verifying webhook payloads

## Webhook Setup

To enable real-time updates, configure GitHub webhooks:

1. Go to your repository/organization settings
2. Navigate to Webhooks
3. Add a new webhook:
   - Payload URL: `https://your-port-instance/api/v1/webhooks/github`
   - Content type: `application/json`
   - Secret: Your configured `webhook_secret`
   - Events: Select the events you want to track (push, pull_request, issues, workflow_run)

## Development

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run tests:
   ```bash
   poetry run pytest
   ```

### Code Style

This project uses:
- Black for code formatting
- Ruff for linting
- MyPy for type checking

Run the linters:
```bash
poetry run black .
poetry run ruff check .
poetry run mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
