import pytest
from dummy_api.routes import RoutesProvider


@pytest.fixture
def route_provider():
    return RoutesProvider("./routes.test.json")

