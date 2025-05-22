import os
import sys
from unittest.mock import MagicMock, AsyncMock
import pytest
from port_ocean.context.ocean import PortOceanContext, initialize_port_ocean_context
from port_ocean.core.integrations.base import BaseIntegration
from port_ocean.exceptions.context import PortOceanContextAlreadyInitializedError

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
    mock_app = MagicMock()
    mock_app.config = MagicMock()
    mock_app.config.client_timeout = 30

    context = PortOceanContext(mock_app)
    context._app = mock_app

    context.http_client = mock_http_client

    mock_integration = MagicMock(spec=BaseIntegration)
    mock_integration.context = context

    mock_app.integration = mock_integration

    context._integration = mock_integration

    try:
        initialize_port_ocean_context(mock_app)
    except PortOceanContextAlreadyInitializedError:
        pass

    return context
