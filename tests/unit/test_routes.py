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


class TestRoutesProviderGet:

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


class TestRoutesProviderPost:

    def get_route_data(self, find_pattern):
        return {
            "routes": [
                {"path": "/test", "name": "test_data", "methods": ["GET"], "data": {"test": 100}},
                {
                    "path": "/test/value",
                    "methods": ["POST"],
                    "data": {"reference": {"source": "test_data", "find": find_pattern}}
                }
            ]
        }

    def setup_method(self):

        self.route_data = {
            "routes": [
                {"path": "/test", "name": "test_data", "methods": ["GET"], "data": {"test": 100}},
                {
                    "path": "/test/value",
                    "methods": ["POST"],
                    "data": {"reference": {"source": "test_data", "find": "test"}}
                }
            ]
        }

    def test_post_route_data_correct_path_update_scalar(self, mocker):
        with mocked_routes_file(mocker, json.dumps(self.route_data)):
            route_provider = RoutesProvider("fake.json")
            result = route_provider.get_route_response_data(
                "/test/value",
                request_method="POST",
                request_body={"payload": 101}
            )
            assert result == {"test": 101}

    def test_post_route_data_correct_path_new_field(self, mocker):
        with mocked_routes_file(mocker, json.dumps(self.get_route_data("."))):
            route_provider = RoutesProvider("fake.json")
            result = route_provider.get_route_response_data(
                "/test/value",
                request_method="POST",
                request_body={"payload": {"new_value": 500}}
            )
            assert result == {"new_value": 500}

