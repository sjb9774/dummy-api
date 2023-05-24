import pytest
from dummy_api.data import DataPathQuery


class TestDataPathQuery:

    def setup_method(self):
        self.dict_to_query = {
            "name": "Test",
            "meta": {
                "name": "Test Dict"
            },
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
                {"id": 3, "name": "Item 3"}
            ],
            "objects_lists": [
                {
                    "id": 100,
                    "name": "Object List 1",
                    "list": [
                        {"name": "Object 1"},
                        {"name": "Object 2"},
                        {"name": "Object 3"}
                    ]
                },
                {
                    "id": 200,
                    "name": "Object List 2",
                    "list": [
                        {"name": "Object 4"},
                        {"name": "Object 5"},
                        {"name": "Object 6"}
                    ]
                }
            ]
        }

    def test_basic_query(self):
        dpq = DataPathQuery("name")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == "Test"

    def test_nested_query(self):
        dpq = DataPathQuery("meta.name")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == "Test Dict"

    def test_list_query_static_value(self):
        dpq = DataPathQuery("items[id=1]")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == {"id": 1, "name": "Item 1"}

    def test_list_query_parameterized_value(self):
        dpq = DataPathQuery("items[id={id}]")
        query_result = dpq.query_dict(self.dict_to_query, id=1)
        assert query_result == {"id": 1, "name": "Item 1"}

    def test_list_query_multi_list_query_static_values(self):
        dpq = DataPathQuery("objects_lists[id=100].list[name='Object 1']")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == {"name": "Object 1"}

    def test_list_query_multi_list_query_parameterized_values(self):
        dpq = DataPathQuery("objects_lists[id={list_id}].list[name={object_name}]")
        query_result = dpq.query_dict(self.dict_to_query, list_id=100, object_name="Object 1")
        assert query_result == {"name": "Object 1"}

    def test_list_query_multi_list_query_mixed_values(self):
        dpq = DataPathQuery("objects_lists[id=100].list[name={object_name}]")
        query_result = dpq.query_dict(self.dict_to_query, object_name="Object 1")
        assert query_result == {"name": "Object 1"}

    def test_list_query_multi_list_query_get_field_result(self):
        dpq = DataPathQuery('objects_lists[id=100].list[name="Object 1"].name')
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == "Object 1"
