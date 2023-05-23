import pytest
from dummy_api.rules import DynamicDataRule, ReferenceDataRule


class TestDynamicDataRules:
    def setup_method(self):
        self.data_resolver = lambda: {"id": 1, "name": "Test", "value": 100}
        self.rule = DynamicDataRule(self.data_resolver)
    
    def test_get_data_lambda(self):
        assert self.rule.get_data() == self.data_resolver()
        assert self.rule.get_data() == {"id": 1, "name": "Test", "value": 100}
    
    def test_get_data_nested_function(self):
        def resolver():
            return {"id": 2, "name": "Test 2"}
        rule = DynamicDataRule(resolver)
        assert rule.get_data() == resolver()
        assert rule.get_data() == {"id": 2, "name": "Test 2"}


class TestReferenceDataRules:
    def setup_method(self):
        self.base_data = {
            "id": 1,
            "name": "Test",
            "value": 100,
            "items": [
                {"id": 100, "name": "Mr. Test"},
                {"id": 200, "name": "Mrs. Test"}
            ]
        }
        self.default_data = {"result": "default"}
        self.data_resolver = lambda: self.base_data
    
    def test_reference_path_simple(self):
        rule = ReferenceDataRule(self.data_resolver, "name", self.default_data)
        assert rule.get_data("") == "Test"

    def test_reference_path_list(self):
        rule = ReferenceDataRule(self.data_resolver, "items.id", self.default_data)
        assert rule.get_data("items/100") == {"id": 100, "name": "Mr. Test"}
    
    def test_reference_path_list_item(self):
        rule = ReferenceDataRule(self.data_resolver, "items.id.name", self.default_data)
        assert rule.get_data("items/100") == "Mr. Test"

    def test_reference_path_list_item_not_exists(self):
        rule = ReferenceDataRule(self.data_resolver, "items.id.name", self.default_data)
        assert rule.get_data("items/1001") == self.default_data
    
    def test_reference_path_invalid_request_path(self):
        rule = ReferenceDataRule(self.data_resolver, "items.id.name", self.default_data)
        assert rule.get_data("items/1001/test/1") == self.default_data

    def test_reference_path_list_non_id(self):
        rule = ReferenceDataRule(self.data_resolver, "items.name", self.default_data)
        assert rule.get_data("items/Mrs. Test") == {"id": 200, "name": "Mrs. Test"}
    
    def test_reference_path_empty(self):  # TODO: throw helpful errors at data-fetching time
        rule = ReferenceDataRule(self.data_resolver, "", self.default_data)
        assert rule.get_data("") == self.default_data
        assert rule.get_data("/anything/at/all") == self.default_data

    def test_reference_path_invalid(self):  # TODO: throw helpful errors at data-fetching time
        rule = ReferenceDataRule(self.data_resolver, "test.id.", self.default_data)
        assert rule.get_data("") == self.default_data
        assert rule.get_data("/anything/at/all") == self.default_data

    def wip_test_create_reference(self):
        Reference = type(object)
        data_provider = lambda: "TBD"
        reference = Reference(data_provider=data_provider, reference_path="data.items.id")
        queried_data = reference.query_data(id=1)