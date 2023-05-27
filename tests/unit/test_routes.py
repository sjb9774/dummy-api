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
                {
                    "path": "/test", "name": "test_data", "methods": ["GET"], "data": {"test": 100}
                },
                {
                    "path": "/test/value",
                    "methods": ["POST"],
                    "data": {"reference": {"source": "test_data", "find": find_pattern}}
                },
                {
                    "path": "/items",
                    "name": "item_data",
                    "methods": ["GET"],
                    "data": {
                        "name": "item_list",
                        "items": [
                            {"id": 100, "value": "Item 1"},
                            {"id": 200, "value": "Item 2"},
                            {"id": 300, "value": "Item 3"}
                        ]
                    }
                },
                {
                    "path": "/items/{id}",
                    "name": "item_data_by_id",
                    "methods": ["GET", "POST"],
                    "data": {
                        "reference": {
                            "source": "item_data",
                            "find": "items[id={id}]"
                        }
                    }
                }
            ]
        }

    def test_post_route_data_correct_path_update_scalar(self, mocker):
        with mocked_routes_file(mocker, json.dumps(self.get_route_data("test"))):
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

    # def test_post_route_data_new_list_item(self, mocker):
    #     with mocked_routes_file(mocker, json.dumps(self.get_route_data("."))):
    #         route_provider = RoutesProvider("fake.json")
    #         get_items_result = route_provider.get_route_response_data(
    #             "/items",
    #             request_method="GET"
    #         )
    #         assert len(get_items_result.get("items")) == 3
    #         get_item_result = route_provider.get_route_response_data(
    #             "/items/100",
    #             request_method="GET"
    #         )
    #         assert get_item_result.get("value") == "Item 1"
    #         post_item_result = route_provider.get_route_response_data(
    #             "/items/100",
    #             request_method="POST",
    #             request_body={"id": 500, "value": "Item 5"}
    #         )
    #         assert post_item_result == {"id": 500, "value": "Item 5"}


