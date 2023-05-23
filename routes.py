import json
from .rules import DynamicDataRule, ReferenceDataRule
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

    def handle(self, request: RouteRequest) -> str:
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
        self.route_rule_chain = self.build_route_rule_chain()

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

    def get_base_rule(self) -> RouteRule:
        rule = DynamicDataRule(lambda: "No data available")
        return RouteRule("*", rule)

    def build_route_rule_chain(self) -> RouteRuleChain:
        rules = self.get_route_rules() + [self.get_base_rule()]
        links = list(map(lambda rule: RouteRuleChainLink(rule), rules))
        return RouteRuleChain(links)

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

    def get_route_response_data(self, request_path, request_method=None, query_parameters=None, request_body=None) -> str:
        request = RouteRequest(
            request_path=request_path,
            request_method=request_method,
            query_parameters=query_parameters,
            request_body=request_body
        )
        return self.route_rule_chain.execute(request) or "Not found"  # TODO: Add baseline rule that handles all requests with "Not found"


class RouteRuleBuilder:
    
    @staticmethod
    def build_rule(path: str, data_resolver: callable) -> RouteRule:
        data_rule = DynamicDataRule(data_resolver)
        return RouteRule(path, data_rule)
    
    @staticmethod
    def build_reference(path: str, data_resolver: callable, reference_path: str, default_data: dict) -> RouteRule:
        data_rule = ReferenceDataRule(data_resolver, reference_path, default_data)
        return RouteRule(path, data_rule)
