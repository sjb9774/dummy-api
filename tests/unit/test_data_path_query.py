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

    def test_root_query(self):
        dpq = DataPathQuery(".")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == self.dict_to_query

    def test_empty_query(self):
        dpq = DataPathQuery("")
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == self.dict_to_query

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

    def test_list_query_multi_list_query_parameterized_values_same_field_name(self):
        dpq = DataPathQuery("objects_lists[name={list_name}].list[name={object_name}]")
        query_result = dpq.query_dict(self.dict_to_query, list_name="Object List 1", object_name="Object 1")
        assert query_result == {"name": "Object 1"}

    def test_list_query_multi_list_query_mixed_values(self):
        dpq = DataPathQuery("objects_lists[id=100].list[name={object_name}]")
        query_result = dpq.query_dict(self.dict_to_query, object_name="Object 1")
        assert query_result == {"name": "Object 1"}

    def test_list_query_multi_list_query_get_field_result(self):
        dpq = DataPathQuery('objects_lists[id=100].list[name="Object 1"].name')
        query_result = dpq.query_dict(self.dict_to_query)
        assert query_result == "Object 1"

    def test_key_query_static_value(self):
        dpq = DataPathQuery("meta.{variable}")
        query_result = dpq.query_dict(self.dict_to_query, variable="name")
        assert query_result == "Test Dict"

    def test_list_query_with_key_query(self):
        dpq = DataPathQuery("objects_lists[id={list_id}].{list_key}")
        query_result = dpq.query_dict(self.dict_to_query, list_id=200, list_key="name")
        assert query_result == "Object List 2"

    def test_multi_key_query(self):
        dpq = DataPathQuery("{key_1}.{key_2}")
        query_result = dpq.query_dict(self.dict_to_query, key_1="meta", key_2="name")
        assert query_result == "Test Dict"

    def test_entirely_parameterized_query(self):
        dpq = DataPathQuery("{key_1}[id={id}].{key_2}[name={name}].{key_3}")
        query_result = dpq.query_dict(
            self.dict_to_query,
            key_1="objects_lists",
            id=100,
            key_2="list",
            name="Object 1",
            key_3="name"
        )
        assert query_result == "Object 1"


class TestDataPathUpdate:

    def setup_method(self):
        self.dict_to_update = {
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

    def test_root_level_scalar_update_static(self):
        dpq = DataPathQuery("name")
        updated_dict = dpq.update_dict(self.dict_to_update, "New Name")
        assert updated_dict.get("name") == "New Name"

    def test_nested_scalar_update_static(self):
        dpq = DataPathQuery("meta.name")
        updated_dict = dpq.update_dict(self.dict_to_update, "New Name")
        assert updated_dict.get("meta").get("name") == "New Name"

    def test_update_create_new_field_static(self):
        dpq = DataPathQuery("meta.new_value")
        result = dpq.update_dict(self.dict_to_update, "My new value")
        assert result.get("meta").get("new_value") == "My new value"

    def test_root_level_dict_replace_update_static(self):
        dpq = DataPathQuery("meta")
        updated_dict = dpq.update_dict(self.dict_to_update, {"name": "New Dict"})
        assert updated_dict.get("meta") == {"name": "New Dict"}

    def test_update_list_item_with_static_parameter(self):
        dpq = DataPathQuery("items[id=1].name")
        result = dpq.update_dict(self.dict_to_update, "Brand new name")
        assert result["items"][0]["name"] == "Brand new name"

    def test_update_list_item_with_templatized_parameter(self):
        dpq = DataPathQuery("items[id={id}].name")
        result = dpq.update_dict(self.dict_to_update, "Brand new name", id=1)
        assert result["items"][0]["name"] == "Brand new name"

    def test_update_list_item_with_multiple_templatized_parameters(self):
        dpq = DataPathQuery("objects_lists[id={id}].list[name={list_name}].name")
        result = dpq.update_dict(self.dict_to_update, "Brand new name", id=200, list_name="Object 4")
        assert result["objects_lists"][1]["list"][0]["name"] == "Brand new name"

    def test_full_data_replace_from_root_fails(self):
        dpq = DataPathQuery("")
        with pytest.raises(ValueError):
            dpq.update_dict(self.dict_to_update, {"name": "New object"})

    def test_update_nonexistent_field_fails(self):
        dpq = DataPathQuery("does.not.exist")
        with pytest.raises(ValueError):
            dpq.update_dict(self.dict_to_update, "any value")

    def test_update_key_query_field_under_key(self):
        dpq = DataPathQuery("{param}.name")
        result = dpq.update_dict(self.dict_to_update, "New name", param="meta")
        assert result.get("meta").get("name") == "New name"

    def test_update_key_query_key_under_field_preexisting(self):
        dpq = DataPathQuery("meta.{param}")
        result = dpq.update_dict(self.dict_to_update, "New name 2", param="name")
        assert result.get("meta").get("name") == "New name 2"

    def test_update_key_query_under_field_new(self):
        dpq = DataPathQuery("meta.{param}")
        result = dpq.update_dict(self.dict_to_update, "New value", param="new_field")
        assert result.get("meta").get("new_field") == "New value"

    def test_update_key_query_then_static_list_query(self):
        dpq = DataPathQuery("{param_1}[id=1].name")
        result = dpq.update_dict(self.dict_to_update, "New name", param_1="items")
        assert result.get("items")[0].get("name") == "New name"

    def test_update_key_query_then_parameterized_list_query(self):
        dpq = DataPathQuery("{param_1}[id={id}].name")
        result = dpq.update_dict(self.dict_to_update, "New name", param_1="items", id=1)
        assert result.get("items")[0].get("name") == "New name"

    def test_update_static_list_query_then_key_query(self):
        dpq = DataPathQuery("items[id=1].{param_1}")
        result = dpq.update_dict(self.dict_to_update, "New name", param_1="name")
        assert result.get("items")[0].get("name") == "New name"

    def test_update_parameterized_list_query_then_key_query(self):
        dpq = DataPathQuery("items[id={id}].{param_1}")
        result = dpq.update_dict(self.dict_to_update, "New name", id=1, param_1="name")
        assert result.get("items")[0].get("name") == "New name"
