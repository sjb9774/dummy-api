import typing
import re
from dummy_api.request import RouteRequest


class DataPathQuery:
    LIST_QUERY_PARAMETER_REGEX = r"\[(?P<query>(?P<field>\w+)=(?P<value>[^\]]+))\]"
    LIST_QUERY_SPLIT_REGEX = r"([\w_]+(?:\[[^\]]+])?)(?:\.|$)"

    def __init__(self, query_string: str):
        self.query_string = query_string

    def has_parameters(self) -> bool:
        return "{" in self.query_string

    def get_parameter_constraints(self) -> dict:
        match_iter = re.finditer(self.LIST_QUERY_PARAMETER_REGEX, self.query_string)
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
        if len(set(kwargs.keys()) - set(self.get_required_parameter_names())) > 0:
            raise ValueError("Missing required parameters in list query")

        query_string = self.get_concrete_query_string(self.query_string, **kwargs)
        query_pieces = re.split(self.LIST_QUERY_SPLIT_REGEX, query_string)
        query_pieces = [x for x in query_pieces if x]
        result = dict_to_query.copy()
        for query_piece in query_pieces:
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

    def get_data(self, request: RouteRequest, *args, **kwargs) -> typing.Any:
        base_data = self.data_provider(request, *args, **kwargs)  # TODO: respect query path and pull appropriate data
        data_path = DataPathQuery(self.query_path)
        return data_path.query_dict(base_data, **kwargs) or self.default

    def __call__(self, request: RouteRequest, *args, **kwargs) -> typing.Any:
        return self.get_data(request, *args, **kwargs)


class ReferenceResolver:
    LIST_QUERY_REGEX = r"\[(?P<query>.+)\]"

    def __init__(self, data_provider: callable, reference_path: str):
        self.data_provider = data_provider
        self.reference_path = reference_path

    def get_tokenized_data_path(self) -> typing.List[str]:
        return self.reference_path.split(".")

    def query_data(self, **kwargs):
        data_to_return = self.data_provider()
        for path_part in self.get_tokenized_data_path():
            is_list_query = re.search(self.LIST_QUERY_REGEX, path_part)
            if not is_list_query:
                data_to_return = data_to_return.get(path_part, {})
            else:
                list_query_raw = is_list_query.group("query")

        if kwargs and isinstance(data_to_return, list):
            for item in data_to_return:
                should_return = True
                for key, value in kwargs.items():
                    if item.get(key) != value:
                        should_return = False
                        break
                if should_return:
                    return item.copy()
        return data_to_return.copy() if hasattr(data_to_return, "copy") else data_to_return

    def __call__(self, *args, **kwargs):
        return self.query_data(**kwargs)


class MutableDataResolver:

    def __init__(self, base_data: dict):
        self.data = base_data.copy()

    def get_dynamic_data_resolver(self, data_path: str):
        def data_resolver():
            return self.get_data_from_path(data_path)

        return data_resolver

    def get_data_from_path(self, data_path: str, copy=True, base_data=None) -> dict:
        data_to_return = base_data if base_data else self.data
        for path_part in self.tokenize_data_path(data_path):
            data_to_return = data_to_return.get(path_part, {})
        return data_to_return.copy() if copy else data_to_return

    def tokenize_data_path(self, data_path: str):
        return data_path.split(".")

    def add_item_to_list(self, list_data_path: str, item_data: dict):
        list_to_add_data: list = self.get_data_from_path(list_data_path, copy=False)
        if not isinstance(list_to_add_data, list):
            raise ValueError(f"Path '{list_data_path}' does not correspond to a list")
        list_to_add_data.append(item_data)

    def tokenize_identifier(self, identifier: str):
        return identifier.split("=", 1)

    def find_identified_item_in_list(self, data_list: list, identifier: str, copy=True) -> dict:
        field, value = self.tokenize_identifier(identifier)
        for item in data_list:
            if str(item.get(field)) == str(value):
                return item.copy() if copy else item
        return {}

    def update_item_in_list(self, list_data_path: str, identifier: str, update_data: dict):
        list_to_add_data: list = self.get_data_from_path(list_data_path, copy=False)
        if not isinstance(list_to_add_data, list):
            raise ValueError(f"Path '{list_data_path}' does not correspond to a list")
        item_to_update = self.find_identified_item_in_list(list_to_add_data, identifier, copy=False)
        item_to_update.update(update_data)

    def remove_item_in_list(self, list_data_path: str, identifier: str):
        pass

    def get_reference_resolver(self, reference_path: str) -> ReferenceResolver:
        return ReferenceResolver(lambda: self.data, reference_path)
