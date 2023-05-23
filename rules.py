import json
import typing


class SimpleDataRule:

    def __init__(self, rule_data: dict):
        self.rule_data = rule_data
    
    def get_default_value(self):
        self.rule_data.get("default", None)
    
    def get_data_set(self):
        return self.rule_data.get("data")
    
    def resolve_data(self):
        return self.get_data_set() or self.get_default_value()

    def get_data(self, *args, **kwargs):
        print(self.rule_data)
        return self.resolve_data()


class DynamicDataRule(SimpleDataRule):
    
    def __init__(self, data_resolver: callable):
        self.data_resolver = data_resolver
    
    def get_data(self, *args, **kwargs) -> str:
        return self.data_resolver()


class ReferenceDataRule(DynamicDataRule):

    def __init__(self, data_resolver: callable, reference_path: str, default_data: dict):
        super().__init__(data_resolver)
        self.reference_path = reference_path
        self.default_data = default_data

    def get_reference_path_pieces(self) -> typing.List[str]:
        return self.reference_path.split(".")
    
    def get_data(self, request_path, *args, **kwargs):
        # TODO: Brittle, refactor to be more robust
        base_data = super().get_data()
        request_path_pieces = request_path.split("/")
        i = 0
        for piece in self.get_reference_path_pieces():
            if piece in base_data:
                base_data = base_data.get(piece)
            elif isinstance(base_data, list):
                for datum in base_data:
                    if str(datum.get(piece)) == request_path_pieces[i]:
                        base_data = datum
                        break
                else:
                    return self.default_data
            else:
                return self.default_data
            i += 1
        return base_data
