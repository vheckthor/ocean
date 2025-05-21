import os
import sys
from unittest.mock import MagicMock, AsyncMock
import pytest
from port_ocean.context.ocean import PortOceanContext, initialize_port_ocean_context
from port_ocean.core.integrations.base import BaseIntegration
from port_ocean.exceptions.context import PortOceanContextAlreadyInitializedError

# Add the Ocean root directory to the Python path
ocean_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, ocean_root)

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.headers = {"X-RateLimit-Remaining": "1000"}
    mock_response.json = AsyncMock(return_value=[])
    client.request.return_value = mock_response
    return client

@pytest.fixture
def mock_ocean_context(mock_http_client):
    """Create a mock Ocean context for testing."""
    # Create a mock app with all required attributes
    mock_app = MagicMock()
    mock_app.config = MagicMock()
    mock_app.config.client_timeout = 30

    # Create and set up the context
    context = PortOceanContext(mock_app)
    context._app = mock_app

    # Set the mock HTTP client
    context.http_client = mock_http_client

    # Create a mock integration
    mock_integration = MagicMock(spec=BaseIntegration)
    mock_integration.context = context

    # Set the integration on the app
    mock_app.integration = mock_integration

    # Set the integration on the context
    context._integration = mock_integration

    # Set the global context for LocalProxy
    try:
        initialize_port_ocean_context(mock_app)
    except PortOceanContextAlreadyInitializedError:
        pass

    return context
