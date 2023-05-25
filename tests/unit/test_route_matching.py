import pytest
from dummy_api.routes import RouteRequest
from dummy_api.route_matching import RouteConstraint


class TestRouteConstraint:

    def test_static_constraint_request_does_match(self):
        path = "/data/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/items",  request_method="GET")
        assert constraint.does_request_match(request)

    def test_static_constraint_does_match_extract_params(self):
        path = "/data/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/items", request_method="GET")
        assert constraint.get_constraint_parameters_from_request(request) == {}

    def test_static_constraint_does_not_match(self):
        path = "/data/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/something_else", request_method="GET")
        assert not constraint.does_request_match(request)

    def test_static_constraint_does_not_match_extract_params(self):
        path = "/data/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/something_else", request_method="GET")
        with pytest.raises(ValueError):
            constraint.get_constraint_parameters_from_request(request)

    def test_static_wildcard_constraint_does_match(self):
        path = "/data/*/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/matchthis/items", request_method="GET")
        assert constraint.does_request_match(request)

    def test_static_wildcard_constraint_does_not_match(self):
        path = "/data/*/items"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/matchthis/dontmatch/items", request_method="GET")
        assert not constraint.does_request_match(request)

    def test_dynamic_constraint_does_match_one_param(self):
        path = "/data/items/{id}"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/items/100",  request_method="GET")
        assert constraint.does_request_match(request)

    def test_dynamic_constraint_does_match_one_param_extract_params(self):
        path = "/data/items/{id}"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/items/100", request_method="GET")
        assert constraint.get_constraint_parameters_from_request(request) == {"id": "100"}

    def test_dynamic_constraint_does_match_multiple_param_extract_params(self):
        path = "/data/{data_type}/items/{id}"
        constraint = RouteConstraint(path)
        request = RouteRequest("/data/people/items/100", request_method="GET")
        assert constraint.get_constraint_parameters_from_request(request) == {"id": "100", "data_type": "people"}