import typing
import re
from dummy_api.request import RouteRequest


class DataPathQuery:
    LIST_QUERY_PARAMETER_REGEX = r"\[(?P<query>(?P<field>\w+)=(?P<value>[^\]]+))\]"
    LIST_QUERY_PARAMETER_CONSTRAINT_REGEX = r"\[(?P<query>(?P<field>\w+)=(?P<value>\{[^\]]+\}))\]"
    LIST_QUERY_SPLIT_REGEX = r"([\w_]+(?:\[[^\]]+])?)(?:\.|$)"
    KEY_QUERY_REGEX = r"(?P<key_value>\{[\w\d_]+\})"

    def __init__(self, query_string: str):
        self.query_string = query_string

    def has_parameters(self) -> bool:
        return "{" in self.query_string

    def get_parameter_constraints(self) -> list:
        match_iter = re.finditer(self.LIST_QUERY_PARAMETER_CONSTRAINT_REGEX, self.query_string)
        result_list = [match.group("value") for match in match_iter] if match_iter else []
        return result_list

    def get_required_parameter_names(self) -> typing.List[str]:
        cleaned_results = [value.strip("{}") for value in self.get_parameter_constraints()]
        return cleaned_results

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

    def validate_params(self, **kwargs):
        passed_params_set = set(kwargs.keys())
        required_params_set = set(self.get_required_parameter_names())
        if len(required_params_set.difference(passed_params_set)) != 0:
            raise ValueError("Missing required parameters in list query")
        return True

    def get_query_tokens(self, **kwargs) -> typing.List[str]:
        query_string = self.get_concrete_query_string(self.query_string, **kwargs)
        query_pieces = re.split(self.LIST_QUERY_SPLIT_REGEX, query_string)
        query_pieces = [x for x in query_pieces if x and x != "."]
        return query_pieces

    def is_root_query(self, **kwargs) -> bool:
        return len(self.get_query_tokens(**kwargs)) == 0

    def get_list_name_and_query_term_from_token(self, token: str) -> typing.List[str]:
        item_name, list_query = token.split("[", 1)
        return [item_name, f"[{list_query}"]

    def update_dict(self, dict_to_update: dict, update_data: typing.Any, **kwargs) -> dict:
        self.validate_params(**kwargs)
        query_pieces = self.get_query_tokens(**kwargs)
        result = dict_to_update
        if not query_pieces:
            raise ValueError("Must provide a query path for updates, cannot replace entire object")
        last_piece = query_pieces[-1]
        for query_piece in query_pieces[:-1]:
            if not result:
                raise ValueError("Could not find value to update")
            if self.is_list_query_term(query_piece):
                item_name, list_query = self.get_list_name_and_query_term_from_token(query_piece)
                try:
                    result = self.resolve_list_query_term(result.get(item_name), list_query, **kwargs)
                except ValueError:
                    return {}
            else:
                result = self.resolve_dict_query_term(result, query_piece, **kwargs)

        if self.is_list_query_term(last_piece):
            item_name, list_query = self.get_list_name_and_query_term_from_token(last_piece)
            item: dict = self.resolve_list_query_term(result.get(item_name), list_query, **kwargs)
            item.clear()  # POST
            item.update(update_data)
            return dict_to_update

        if result and last_piece in result and isinstance(result[last_piece], list):
            # Introspecting the types of data here to make a guess at whether we are posting a new "entity"
            # or replacing a field value. Life would be easier if we draw a clear line between PUT and POST behaviors.
            # ie POST will ALWAYS append to arrays, PUT will always replace (may seem backwards but bear in mind that
            # POSTing will primarily be done against entity list routes where it makes sense that it should append).
            # May be most cleanly resolved by adding new route properties, perhaps defining array/dict behavior with
            # append/extend rules. Requires more routes but gives more control.
            if len(result[last_piece]) > 0 and isinstance(result[last_piece][0], dict):
                result[last_piece].append(update_data)
            else:
                result[last_piece] = update_data
        else:
            result[last_piece] = update_data

        return dict_to_update

    def is_key_query_term(self, query_piece) -> bool:
        return bool(re.search(self.KEY_QUERY_REGEX, query_piece))

    def get_key_query_pieces(self, query_piece) -> str:
        m = re.match(self.KEY_QUERY_REGEX, query_piece)
        if m is None:
            raise ValueError("Could not parse key value out of string")
        return m.group("key_value")

    def resolve_key_query_term(self, dict_to_query: dict, key_value_term: str, **kwargs) -> typing.Any:
        return dict_to_query.get(kwargs.get(key_value_term.strip("{}")))

    def query_dict(self, dict_to_query: dict, copy=True, **kwargs):
        self.validate_params(**kwargs)

        query_pieces = self.get_query_tokens(**kwargs)
        result = dict_to_query.copy() if copy else dict_to_query
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
            elif self.is_key_query_term(query_piece):
                item_name, key_value = self.get_key_query_pieces(query_piece)
                result = self.resolve_key_query_term(result.get(item_name), key_value, **kwargs)
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
        return self.default if result is None else result

    def __call__(self, **kwargs) -> typing.Any:
        return self.get_data(**kwargs)


class DataMutator:

    def __init__(
            self,
            data_ref_provider: callable,
            delete_fn: callable = None,
            replace_fn: callable = None,
            query_path: str = ""
    ):
        self.data_ref_provider = data_ref_provider
        self.delete_fn = delete_fn
        self.replace_fn = replace_fn
        self.query_path = query_path

    def get_data(self, **kwargs) -> dict:
        base_data = self.data_ref_provider()  # TODO: respect query path and pull appropriate data
        data_path = DataPathQuery(self.query_path)
        return data_path.query_dict(base_data, copy=False, **kwargs)

    def get_object_to_update(self, **kwargs) -> dict:
        base_data = self.data_ref_provider(**kwargs)

    def update_data(self, new_data: dict, **kwargs) -> dict:
        data_path = DataPathQuery(self.query_path)
        if data_path.is_root_query(**kwargs):
            return self.replace_fn(new_data)

        next_to_last_query_path = ".".join(self.query_path.split(".")[:-1])
        next_to_last_data_path = DataPathQuery(next_to_last_query_path)
        # base_data = next_to_last_data_path.query_dict(self.data_ref_provider(), copy=False, **kwargs)

        updated_data_source = data_path.update_dict(self.data_ref_provider(), new_data, **kwargs)
        return next_to_last_data_path.query_dict(updated_data_source, **kwargs)

    def delete(self) -> None:
        return self.delete_fn()

    def replace(self, new_data: dict) -> dict:
        return self.replace_fn(new_data)


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

    def get_mutator_delete(self, group_name: str) -> callable:
        def mutator_delete() -> None:
            del self.data_groups[group_name]
            return None

        return mutator_delete

    def get_mutator_replace(self, group_name: str) -> callable:
        def mutator_update(new_data: dict) -> dict:
            self.data_groups[group_name] = new_data
            return self.data_groups.get(group_name)

        return mutator_update

    def get_group_mutator(self, name: str, query_path: str = "") -> DataMutator:
        return DataMutator(
            lambda: self.data_groups.get(name),
            query_path=query_path,
            delete_fn=self.get_mutator_delete(name),
            replace_fn=self.get_mutator_replace(name)
        )

    def get_resolver_by_name(self, name: str) -> DataResolver:
        if not self.does_resolver_exist(name):
            raise ValueError(f"Data resolver '{name}' does not exist")
        return self.data_resolvers.get(name)

    def does_resolver_exist(self, name: str) -> bool:
        return name in self.data_resolvers
