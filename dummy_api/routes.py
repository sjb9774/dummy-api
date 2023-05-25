import json
from dummy_api.rules import DynamicDataRule, ReferenceDataRule
from dummy_api.data import MutableDataStore, DataResolver
from dummy_api.route_matching import RouteConstraint
from dummy_api.request import RouteRequest
import typing


class Route:
    def __init__(self, constraint: RouteConstraint, data_resolver: DataResolver):
        self.constraint = constraint
        self.data_resolver = data_resolver

    def can_handle_request(self, request: RouteRequest) -> bool:
        return self.constraint.does_request_match(request)

    def get_data(self, request: RouteRequest) -> typing.Any:
        kwargs = self.constraint.get_constraint_parameters_from_request(request)
        return self.data_resolver(request, **kwargs)


class RouteRule:

    def __init__(self, route_path: str, data_rule: DynamicDataRule):
        self.route_path = route_path.lstrip("/")
        self.data_rule = data_rule

    def get_route_data(self, request: RouteRequest) -> dict:
        return self.data_rule.get_data(
            request.get_request_path(),
            request_method=request.get_request_method(),
            query_parameters=request.get_query_params(),
            request_body=request.get_request_body()
        )

    def get_route_path(self) -> str:
        return self.route_path

    @staticmethod
    def normalize_request_path(request_path: str):
        return request_path.strip("/")

    def can_handle_request(self, request: RouteRequest) -> bool:
        return self.does_request_path_match_route(request.get_request_path())

    def does_request_path_match_route(self, request_path: str) -> bool:
        request_path = self.normalize_request_path(request_path)
        tokenized_request = self.tokenize_request_path(request_path)
        tokenized_route = self.get_tokenized_route_path()

        for i in range(len(tokenized_route)):
            route_token = tokenized_route[i]
            if route_token == "*":
                return True
            if i > len(tokenized_request):
                return False
            request_token = tokenized_request[i]
            if not route_token.startswith("{") and route_token != request_token:
                return False
        if len(tokenized_request) > i + 1:
            return False
        return True

    def tokenize_request_path(self, request_path: str):
        return request_path.split("/")

    def get_tokenized_route_path(self):
        return self.route_path.split("/")

    @staticmethod
    def is_reference_rule(rule_config: dict) -> bool:
        return "reference" in rule_config.get("data", {})


class RouteRuleChainLink:

    def __init__(self, route_rule: RouteRule) -> None:
        self.route_rule = route_rule

    def can_handle(self, request: RouteRequest) -> bool:
        return self.route_rule.can_handle_request(request)

    def handle(self, request: RouteRequest) -> typing.Any:
        return self.route_rule.get_route_data(request)


class RouteRuleChain:

    def __init__(self, rules: typing.List[RouteRuleChainLink]) -> None:
        self.rule_chain_link = rules

    def execute(self, request: RouteRequest):
        for rule_link in self.rule_chain_link:
            if rule_link.can_handle(request):
                return rule_link.handle(request)


class RoutesProvider:

    def __init__(self, file_path: str):
        self.named_data_references = {}
        self.file_path = file_path
        self.raw_route_data = self.get_data_file_contents(self.file_path)
        self.main_data_store = MutableDataStore()
        self.routes = self.build_routes()

    @staticmethod
    def get_data_file_contents(file_path: str) -> dict:
        with open(file_path, "r") as f:
            return json.loads(f.read())

    def get_data_resolver(self, data: dict) -> callable:
        base_data = data.get("data")
        if base_data.get("reference"):
            reference_data = base_data.get("reference")
            referenced_data_source = reference_data.get("source")

            def reference_resolver():
                referenced_data_resolver = self.named_data_references[referenced_data_source]
                return referenced_data_resolver()

            return reference_resolver

        def basic_resolver(request: RouteRequest, *args, **kwargs):
            return base_data

        return basic_resolver

    def build_routes(self) -> typing.List[Route]:
        routes = []
        for route_config_entry in self.raw_route_data.get("routes", []):
            path = route_config_entry.get("path")
            name = route_config_entry.get("name")
            route_data = route_config_entry.get("data")
            # TODO: Improve delineation between simple "data" routes and reference routes
            if not route_data.get("reference"):  # not a reference, has raw data to provide
                self.main_data_store.add_data_group(name, route_data)

            resolver = self.main_data_store.build_data_resolver(
                route_data.get("reference", {}).get("source", name),
                route_data.get("reference", {}).get("find", "")
            )  # build resolver that may pull from another data source
            # add resolver under its own name so it can also be referenced
            self.main_data_store.add_resolver(name, resolver)

            route = Route(RouteConstraint(path, ["GET"]), resolver)
            routes.append(route)

        routes.append(self.get_default_route())

        return routes

    @staticmethod
    def get_default_response_data(request: RouteRequest, *args, **kwargs):
        return {"error": True, "message": "Not found"}
    @staticmethod
    def get_default_route() -> Route:
        default_constraint = RouteConstraint("/*")
        default_resolver = DataResolver("default_route", RoutesProvider.get_default_response_data)
        route = Route(default_constraint, default_resolver)
        return route

    def handle_request(self, request: RouteRequest) -> typing.Any:
        for route in self.routes:
            if route.can_handle_request(request):
                return route.get_data(request) or RoutesProvider.get_default_response_data(request)

    def get_route_response_data(self, request_path, request_method=None, query_parameters=None,
                                request_body=None) -> typing.Any:
        request = RouteRequest(
            request_path=request_path,
            request_method=request_method,
            query_parameters=query_parameters,
            request_body=request_body
        )
        return self.handle_request(request)


class RouteRuleBuilder:

    @staticmethod
    def build_rule(path: str, data_resolver: callable) -> RouteRule:
        data_rule = DynamicDataRule(data_resolver)
        return RouteRule(path, data_rule)

    @staticmethod
    def build_reference(path: str, data_resolver: callable, reference_path: str, default_data: dict) -> RouteRule:
        data_rule = ReferenceDataRule(data_resolver, reference_path, default_data)
        return RouteRule(path, data_rule)
