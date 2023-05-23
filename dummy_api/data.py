import typing


class ReferenceResolver:

    def __init__(self, data_provider: callable, reference_path: str):
        self.data_provider = data_provider
        self.reference_path = reference_path

    def __call__(self, *args, **kwargs):
        data = self.data_provider()
        #  TODO: Resolve data from path with optional kwargs
        return data


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
        return ReferenceResolver(lambda: self.base_data, reference_path)
