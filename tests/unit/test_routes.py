import pytest
from dummy_api.routes import RoutesProvider, RouteRequest
from contextlib import contextmanager
import json


@contextmanager
def mocked_routes_file(mocker, return_data='{}'):
    mock_open = mocker.patch('dummy_api.routes.open')
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.return_value = return_data
    yield


@pytest.fixture
def route_data_with_reference_path():
    data = {
        "routes": [
            {
                "path": "/test",
                "name": "values",
                "data": {
                    "items": [
                        {"id": 5, "value": "test"}
                    ]
                }
            },
            {
                "path": "/ref/{id}",
                "data": {
                    "reference": {
                        "source": "values",
                        "find": "items[id={id}]"
                    }
                }
            }
        ]
    }
    return json.dumps(data)


class TestRoutesProvider:

    def test_simple_route_provider_init(self, mocker):
        with mocked_routes_file(mocker, '{"routes": []}'):
            route_provider = RoutesProvider("fake.json")
            assert route_provider

    def test_route_provider_default_route(self, mocker):
        with mocked_routes_file(mocker, '{"routes": []}'):
            route_provider = RoutesProvider("fake.json")
            default_route = route_provider.get_default_route()
            assert default_route.get_data(RouteRequest("/")) == {'error': True, 'message': 'Not found'}

    def test_get_route_data_correct_path(self, mocker):
        with mocked_routes_file(mocker, '{"routes": [{"path": "/test", "data": {"test": 100}}]}'):
            route_provider = RoutesProvider("fake.json")
            result = route_provider.get_route_response_data("/test", request_method="GET")
            assert result == {"test": 100}

    def test_get_route_data_incorrect_path(self, mocker):
        with mocked_routes_file(mocker, '{"routes": [{"path": "/test", "data": {"test": 100}}]}'):
            route_provider = RoutesProvider("fake.json")
            result = route_provider.get_route_response_data("/incorrect_path", request_method="GET")
            assert result != {"test": 100}
            assert result == {"error": True, "message": "Not found"}

    def test_get_route_data_reference_path_matching_request(self, mocker, route_data_with_reference_path):
        with mocked_routes_file(mocker, route_data_with_reference_path):
            route_provider = RoutesProvider("fake.json")
            result = route_provider.get_route_response_data("/ref/5", request_method="GET")
            assert result == {"id": 5, "value": "test"}
