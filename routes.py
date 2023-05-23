import json
from .rules import  DynamicDataRule, SimpleDataRule, ReferenceDataRule
import typing


class RouteRequest:

    def __init__(
        self,
        request_path: str = None,
        request_method: str = None,
        query_parameters: dict = {},
        request_body: dict = {}
    ):
        self.request_path = request_path
        self.request_method = request_method
        self.query_parameters = query_parameters
        self.request_body = request_body
    
    def get_query_params(self) -> dict:
        return self.query_parameters.copy()
    
    def get_request_path(self) -> str:
        return self.request_path
    
    def get_request_method(self) -> str:
        return self.request_method
    
    def get_request_body(self) -> dict:
        return self.request_body


class RouteRule:

    def __init__(self, route_path: str, data_rule: SimpleDataRule):
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
        if len(tokenized_request) != len(tokenized_route):
            return False
        
        for i in range(len(tokenized_request)):
            request_token = tokenized_request[i]
            route_token = tokenized_route[i]
            if not route_token.startswith("{") and route_token != request_token:
                return False
        return True
    
    def tokenize_request_path(self, request_path: str):
        return request_path.split("/")
    
    def get_tokenized_route_path(self):
        return self.route_path.split("/")
    
    @staticmethod
    def is_reference_rule(rule_config: dict) -> bool:
        return "reference" in rule_config.get("data", {})


class RoutesProvider:

    def __init__(self, file_path: str):
        self.named_data_references = {}
        self.file_path = file_path
        self.raw_route_data = self.get_data_file_contents(self.file_path)
        self.route_rules = self.get_route_rules()

    @staticmethod
    def get_data_file_contents(file_path: str):
        with open(file_path, "r") as f:
            return json.loads(f.read())

    def get_data_resolver(self, data):
        base_data = data.get("data")
        if base_data.get("reference"):
            reference_data = base_data.get("reference")
            referenced_data_source = reference_data.get("source")
            referenced_resolver = self.named_data_references[referenced_data_source]
            return lambda: referenced_resolver()
        return lambda: base_data

    def get_route_rules(self) -> typing.List[RouteRule]:
        rules_list = []
        for route_config_entry in self.raw_route_data.get("routes", []):
            path = route_config_entry.get("path")
            name = route_config_entry.get("name")  # TODO: Track name for references
            route_data = route_config_entry.get("data")
            data_resolver =  self.get_data_resolver(route_config_entry)
            is_reference = RouteRule.is_reference_rule(route_config_entry)
            if is_reference:
                rule = RouteRuleBuilder.build_reference(
                    path,
                    data_resolver,
                    route_data.get("reference").get("find"),
                    route_config_entry.get("default", {})
                )
            else:
                rule = RouteRuleBuilder.build_rule(path, data_resolver)
            self.named_data_references[name] = data_resolver
            rules_list.append(rule)
        return rules_list

    def handle_rule_chain(self):
        pass

    def get_route_response_data(self, request_path, request_method=None, query_parameters=None, request_body=None) -> str:
        request = RouteRequest(
            request_path=request_path,
            request_method=request_method,
            query_parameters=query_parameters,
            request_body=request_body
        )
        for rule in self.route_rules:
            if rule.can_handle_request(request):
                return rule.get_route_data(request)
        return "Not found"


class RouteRuleBuilder:
    
    @staticmethod
    def build_rule(path: str, data_resolver: callable) -> RouteRule:
        data_rule = DynamicDataRule(data_resolver)
        return RouteRule(path, data_rule)
    
    @staticmethod
    def build_reference(path: str, data_resolver: callable, reference_path: str, default_data: dict) -> RouteRule:
        data_rule = ReferenceDataRule(data_resolver, reference_path, default_data)
        return RouteRule(path, data_rule)
