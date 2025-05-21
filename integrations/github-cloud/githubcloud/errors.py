from port_ocean.exceptions.core import OceanAbortException

class GitHubTokenNotFoundException(OceanAbortException):
    """Raised when GitHub token is not found in configuration."""
    pass

class GitHubWebhookError(OceanAbortException):
    """Raised when there's an error with GitHub webhook setup or handling."""
    pass

class GitHubRateLimitError(OceanAbortException):
    """Raised when GitHub API rate limit is exceeded."""
    pass

class GitHubAuthenticationError(OceanAbortException):
    """Raised when GitHub authentication fails."""
    pass
