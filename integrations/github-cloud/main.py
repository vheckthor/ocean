from port_ocean.core.integrations.base import BaseIntegration
from port_ocean.context.ocean import PortOceanContext

from githubcloud.integration import GitHubIntegration

def init_integration(context: PortOceanContext) -> BaseIntegration:
    """Initialize the GitHub Cloud integration."""
    return GitHubIntegration(context)
