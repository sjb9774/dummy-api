import pytest
import json
import os
from dummy_api.routes import RoutesProvider


@pytest.fixture
def route_provider():
    return RoutesProvider(os.path.join(os.path.dirname(__file__), "routes.test.json"))


class TestRoutesProvider:

    def setup_method(self):
        with open(os.path.join(os.path.dirname(__file__), "routes.test.json"), "r") as f:
            self.raw_data = json.loads(f.read())

    def test_routes_basic_fetch(self, route_provider):
        result = route_provider.get_route_response_data("/friends")
        assert set(result.keys()) == {"friends", "groups"}
        assert self.raw_data.get("routes")[0].get("data") == result

    def test_route_reference(self, route_provider):
        assert route_provider.get_route_response_data("/friends/1").get("first_name") == "Stephen"

    def test_route_reference_trailing_slash(self, route_provider):
        assert route_provider.get_route_response_data("/friends/1/").get("first_name") == "Stephen"

    def test_route_reference_no_preceding_slash(self, route_provider):
        assert route_provider.get_route_response_data("friends/1/").get("first_name") == "Stephen"

    def test_route_reference_not_found(self, route_provider):
        assert route_provider.get_route_response_data("/friends/101").get("message") == "Not found"

    def test_route_unknown_route(self, route_provider):
        result = route_provider.get_route_response_data("/undefined")
        assert result == {"error": True, "message": "Not found"}

    def test_unknown_subpath_of_known_route(self, route_provider):
        result = route_provider.get_route_response_data("/friends/10/something")
        assert result == {"error": True, "message": "Not found"}


