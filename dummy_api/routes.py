import json
from dummy_api.data import MutableDataStore, DataResolver, DataMutator
from dummy_api.route_matching import RouteConstraint
from dummy_api.request import RouteRequest
import typing


class Route:
    def __init__(self, constraint: RouteConstraint, data_resolver: DataResolver, data_mutator: DataMutator = None):
        self.constraint = constraint
        self.data_resolver = data_resolver
        self.data_mutator = data_mutator

    def can_handle_request(self, request: RouteRequest) -> bool:
        return self.constraint.does_request_match(request)

    def handle_request(self, request: RouteRequest) -> typing.Any:
        if request.get_request_method() == "GET":
            return self.get_data(request)
        elif request.get_request_method() == "POST":
            return self.post_data(request)

    def post_data(self, request: RouteRequest) -> dict:
        kwargs = self.constraint.get_constraint_parameters_from_request(request)
        return self.data_mutator.update_data(request.get_request_body().get("payload"), **kwargs)

    def get_data(self, request: RouteRequest) -> typing.Any:
        kwargs = self.constraint.get_constraint_parameters_from_request(request)
        return self.data_resolver(**kwargs)


class RoutesProvider:

    def __init__(self, file_path: str):
        self.named_data_references = {}
        self.file_path = file_path
        self.raw_route_data = self.get_data_file_contents(self.file_path)
        self.main_data_store = MutableDataStore()
        self.populate_data_groups()
        self.routes = self.build_routes()

    @staticmethod
    def get_data_file_contents(file_path: str) -> dict:
        with open(file_path, "r") as f:
            return json.loads(f.read())

    def populate_data_groups(self):
        for group_dict in self.raw_route_data.get("data_groups", []):
            self.main_data_store.add_data_group(group_dict.get("group_name"), group_dict.get("data"))

    def build_routes(self) -> typing.List[Route]:
        routes = []
        for route_config_entry in self.raw_route_data.get("routes", []):
            path = route_config_entry.get("path")
            name = route_config_entry.get("name")
            route_data = route_config_entry.get("data")

            group_name = route_data.get("reference", {}).get("source", name)
            query_path = route_data.get("reference", {}).get("find", "")
            resolver = self.main_data_store.build_data_resolver(
                group_name,
                query_path
            )  # build resolver that may pull from another data source
            mutator = self.main_data_store.get_group_mutator(group_name, query_path)
            # add resolver under its own name so it can also be referenced
            self.main_data_store.add_resolver(name, resolver)

            route = Route(
                RouteConstraint(path, route_config_entry.get("methods", ["GET"])),
                resolver,
                mutator
            )
            routes.append(route)

        routes.append(self.get_default_route())

        return routes

    @staticmethod
    def get_default_response_data():
        return {"error": True, "message": "Not found"}

    @staticmethod
    def get_default_route() -> Route:
        default_constraint = RouteConstraint("/**")
        default_resolver = DataResolver("default_route", RoutesProvider.get_default_response_data)
        route = Route(default_constraint, default_resolver)
        return route

    def handle_request(self, request: RouteRequest) -> typing.Any:
        for route in self.routes:
            if route.can_handle_request(request):
                return route.handle_request(request) or RoutesProvider.get_default_response_data()

    def get_route_response_data(self, request_path, request_method=None, query_parameters=None,
                                request_body=None) -> typing.Any:
        request = RouteRequest(
            request_path=request_path,
            request_method=request_method,
            query_parameters=query_parameters,
            request_body=request_body
        )
        return self.handle_request(request)
