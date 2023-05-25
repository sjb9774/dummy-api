import typing
import re
from dummy_api.request import RouteRequest


class DataPathQuery:
    LIST_QUERY_PARAMETER_REGEX = r"\[(?P<query>(?P<field>\w+)=(?P<value>[^\]]+))\]"
    LIST_QUERY_PARAMETER_CONSTRAINT_REGEX = r"\[(?P<query>(?P<field>\w+)=(?P<value>\{[^\]]+\}))\]"
    LIST_QUERY_SPLIT_REGEX = r"([\w_]+(?:\[[^\]]+])?)(?:\.|$)"

    def __init__(self, query_string: str):
        self.query_string = query_string

    def has_parameters(self) -> bool:
        return "{" in self.query_string

    def get_parameter_constraints(self) -> dict:
        match_iter = re.finditer(self.LIST_QUERY_PARAMETER_CONSTRAINT_REGEX, self.query_string)
        return {match.group("field"): match.group("value") for match in match_iter} if match_iter else {}

    def get_required_parameter_names(self):
        return [value.strip("{}") for value in self.get_parameter_constraints().values()]

    @staticmethod
    def get_concrete_query_string(parameterized_query_string: str, **kwargs) -> str:
        concrete_query_string = parameterized_query_string
        for field, value in kwargs.items():
            #  TODO: Better handle non-string data
            concrete_query_string = concrete_query_string.replace("{" + field + "}", str(value))
        return concrete_query_string

    def is_list_query_term(self, query_term: str) -> bool:
        return bool(re.search(self.LIST_QUERY_PARAMETER_REGEX, query_term))

    def resolve_dict_query_term(self, data_to_query: dict, query_term: str, **kwargs) -> typing.Any:
        return data_to_query.get(query_term)

    def normalized_query_compare(self, data_value: typing.Any, queried_value: str) -> bool:
        normalized_queried_value = queried_value
        return data_value == normalized_queried_value

    def get_concrete_query_value(self, query_request_value: str, **kwargs):
        is_parameterized_value = "{" in query_request_value
        if is_parameterized_value:
            return kwargs.get(query_request_value.strip("{}"))
        if query_request_value.isdigit():
            return int(query_request_value)
        return query_request_value.strip("'\"")

    def resolve_list_query_term(self, list_to_query: typing.List[dict], query_term, **kwargs) -> typing.Any:
        parameter_match = re.search(self.LIST_QUERY_PARAMETER_REGEX, query_term)
        for item in list_to_query:
            query_requested_field = parameter_match.group("field")
            query_requested_value = parameter_match.group("value")
            concrete_value = self.get_concrete_query_value(query_requested_value, **kwargs)
            if self.normalized_query_compare(item.get(query_requested_field), concrete_value):
                return item
        raise ValueError("Matching value not found in list")

    def query_dict(self, dict_to_query: dict, **kwargs):
        passed_params_set = set(kwargs.keys())
        required_params_set = set(self.get_required_parameter_names())
        if len(passed_params_set.symmetric_difference(required_params_set)) != 0:
            raise ValueError("Missing required parameters in list query")

        query_string = self.get_concrete_query_string(self.query_string, **kwargs)
        query_pieces = re.split(self.LIST_QUERY_SPLIT_REGEX, query_string)
        query_pieces = [x for x in query_pieces if x]
        result = dict_to_query.copy()
        for query_piece in query_pieces:
            if not result:
                return None
            if self.is_list_query_term(query_piece):
                # TODO: This logic is a bit gross, use cleaner pattern matching
                item_name, list_query = query_piece.split("[", 1)
                try:
                    result = self.resolve_list_query_term(result.get(item_name), f"[{list_query}", **kwargs)
                except ValueError:
                    return None
            else:
                result = self.resolve_dict_query_term(result, query_piece, **kwargs)
        return result


class DataResolver:

    def __init__(self, name: str, data_provider: callable, query_path: str = "", default=None):
        self.name = name
        self.data_provider = data_provider
        self.query_path = query_path
        self.default = default

    def get_data(self, **kwargs) -> typing.Any:
        base_data = self.data_provider(**kwargs)  # TODO: respect query path and pull appropriate data
        data_path = DataPathQuery(self.query_path)
        result = data_path.query_dict(base_data, **kwargs)
        return self.default if result is None else data_path.query_dict(base_data, **kwargs)

    def __call__(self, **kwargs) -> typing.Any:
        return self.get_data(**kwargs)


class DataMutator:

    def __init__(self, hard_data_reference: dict):
        self.data_reference = hard_data_reference

    def get_data(self) -> dict:
        return self.data_reference


class MutableDataStore:

    def __init__(self):
        self.data_resolvers = {}
        self.data_groups = {}

    def build_data_resolver(self, name: str, query_path: str = "") -> DataResolver:
        def data_resolver_fn(**kwargs) -> typing.Any:
            return self.data_groups.get(name)

        resolver = DataResolver(name, data_resolver_fn, query_path)
        return resolver

    def add_data_group(self, name: str, data: dict):
        self.data_groups[name] = data
        return self

    def build_resolver_for_data_group(self, data_group_name: str, data_group_data: dict, query_path: str = ""):
        def data_resolver_fn(**kwargs) -> typing.Any:
            return self.data_groups.get(data_group_name)

        self.add_data_group(data_group_name, data_group_data)
        resolver = DataResolver(data_group_name, data_resolver_fn, query_path)
        self.add_resolver(data_group_name, resolver)
        return resolver

    def add_resolver(self, name: str, resolver: DataResolver):
        self.data_resolvers[name] = resolver

    def get_group_mutator(self, name) -> DataMutator:
        return DataMutator(self.data_groups.get(name))

    def get_resolver_by_name(self, name: str) -> DataResolver:
        if not self.does_resolver_exist(name):
            raise ValueError(f"Data resolver '{name}' does not exist")
        return self.data_resolvers.get(name)

    def does_resolver_exist(self, name: str) -> bool:
        return name in self.data_resolvers
