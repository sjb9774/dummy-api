import pytest
import json
import os
from dummy_api.routes import RoutesProvider


@pytest.fixture
def route_provider():
    return RoutesProvider(os.path.join(os.path.dirname(__file__), "routes.test.json"))


class TestRoutesProviderGet:

    def setup_method(self):
        with open(os.path.join(os.path.dirname(__file__), "routes.test.json"), "r") as f:
            self.raw_data = json.loads(f.read())

    def test_routes_basic_fetch(self, route_provider):
        result = route_provider.get_route_response_data("/friends")
        assert set(result.keys()) == {"friends", "groups", "meta"}
        assert self.raw_data.get("data_groups")[0].get("data") == result

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


class TestRoutesProviderPost:

    def setup_method(self):
        with open(os.path.join(os.path.dirname(__file__), "routes.test.json"), "r") as f:
            self.raw_data = json.loads(f.read())

    def test_post_json_to_data_list(self, route_provider):
        payload = {
            "id": 3,
            "first_name": "Robert",
            "last_name": "Stevenson",
            "friend_since": "1850-11-13",
            "tags": ["old", "nautical", "spooky"]
        }
        result = route_provider.get_route_response_data(
            "/friends",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("friends")[-1] == payload

    def test_post_json_to_json(self, route_provider):
        payload = {
            "name": "New test data",
            "value": 5000,
            "new_field": True
        }
        result = route_provider.get_route_response_data(
            "/meta",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("meta") == payload

    def test_post_scalar_to_scalar(self, route_provider):  # TODO: Seems identical to what "PUT" should do?
        payload = "Brand new value"
        result = route_provider.get_route_response_data(
            "/meta_name",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("name") == payload

    def test_post_scalar_to_json(self, route_provider):
        payload = "Brand new value"
        result = route_provider.get_route_response_data(
            "/meta",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("meta") == payload

    def test_post_json_to_scalar(self, route_provider):
        payload = {"value": "Brand new value"}
        result = route_provider.get_route_response_data(
            "/meta_name",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("name") == payload

    def test_post_list_to_list(self, route_provider):
        payload = [
            {
                "name": "New item"
            }
        ]
        result = route_provider.get_route_response_data(
            "/friends",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("friends")[-1] == payload

    def test_post_list_to_json(self, route_provider):
        payload = ["new", "tag", "values"]
        result = route_provider.get_route_response_data(
            "/friends/1/tags",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("tags") == payload

    def test_post_scalar_to_list(self, route_provider):
        payload = "new value"
        result = route_provider.get_route_response_data(
            "/friends",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("friends")[-1] == payload

    def test_post_field_update_multi_parameter_refernce(self, route_provider):  # TODO: Should be relegated to PUT?
        payload = "New Value"
        result = route_provider.get_route_response_data(
            "/groups/100/members/1",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("name") == payload

    def test_post_json_to_reference_route(self, route_provider):  # TODO: Is this "good" behavior?
        payload = {
            "value": 100,
            "name": "New Value"
        }
        result = route_provider.get_route_response_data(
            "/friends/1",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )
        assert result.get("friends")[0] == payload


class TestDynamicRoute:

    def setup_method(self):
        with open(os.path.join(os.path.dirname(__file__), "routes.test.json"), "r") as f:
            self.raw_data = json.loads(f.read())

    def test_get_empty_data_default(self, route_provider):
        result = route_provider.get_route_response_data(
            "/data/entities",
            request_method="GET"
        )
        assert result == {}

    def test_create_and_fetch_json_data(self, route_provider):
        payload = {"value": 100}
        result_1 = route_provider.get_route_response_data(
            "/data/entities",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )

        assert result_1.get("entities") == payload
        result_2 = route_provider.get_route_response_data(
            "/data/entities",
            request_method="GET"
        )

        assert result_2 == payload

    def test_create_entity_list_and_fetch_by_id(self, route_provider: RoutesProvider):
        payload = [{"id": 1, "name": "Stephen", "value": "Test"}]
        result_1 = route_provider.get_route_response_data(
            "/data/entities",
            request_method="POST",
            request_body={
                "payload": payload
            }
        )

        assert result_1.get("entities") == payload

        result_2 = route_provider.get_route_response_data(
            "/data/entities/1",
            request_method="GET"
        )

        assert result_2 == payload[0]

