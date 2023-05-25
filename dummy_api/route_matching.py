import typing
from dummy_api.request import RouteRequest


class RouteConstraint:

    def __init__(self, route_pattern: str, request_methods=None):
        self.route_pattern = route_pattern
        self.request_methods = request_methods or ["GET", "PATCH", "PUT", "POST", "DELETE"]

    def does_request_match(self, route_request: RouteRequest) -> bool:
        if route_request.get_request_method() not in self.request_methods:
            return False

        return RouteMatcher.does_request_path_match_route_pattern(
            route_request.get_request_path(),
            self.route_pattern
        )

    def get_constraint_parameters_from_request(self, request: RouteRequest) -> dict:
        if not self.does_request_match(request):
            raise ValueError("Can't extract parameters for request that doesn't match constraint")
        request_path_pieces = request.get_request_path().split("/")
        route_pattern_pieces = self.route_pattern.split("/")
        params = {}

        for i in range(len(route_pattern_pieces)):
            route_token = route_pattern_pieces[i]
            if route_token == "*":
                continue
            request_token = request_path_pieces[i]
            if route_token.startswith("{"):
                params[route_token.strip("{}")] = request_token

        return params


class RouteMatcher:

    @staticmethod
    def normalize_request_path(request_path: str):
        return request_path.strip("/")

    @staticmethod
    def tokenize_request_path(request_path: str):
        return request_path.strip("/").split("/")

    @staticmethod
    def tokenize_route_pattern(route_pattern) -> typing.List[str]:
        return route_pattern.strip("/").split("/")

    @staticmethod
    def does_request_path_match_route_pattern(request_path, route_pattern) -> bool:
        request_path = RouteMatcher.normalize_request_path(request_path)
        tokenized_request = RouteMatcher.tokenize_request_path(request_path)
        tokenized_route = RouteMatcher.tokenize_route_pattern(route_pattern)

        for i in range(len(tokenized_route)):
            route_token = tokenized_route[i]
            if route_token == "*":
                continue
            if i > len(tokenized_request):
                return False
            request_token = tokenized_request[i]
            if not route_token.startswith("{") and route_token != request_token:
                return False
        if len(tokenized_request) > i + 1:  # are there further unmatched tokens?
            return False
        return True
