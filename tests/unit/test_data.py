import pytest
from dummy_api.data import MutableDataResolver

base_data = {
    "routes": [
        {
            "path": "/beers",
            "name": "beers",
            "default": {
                "error": True,
                "message": "Not found"
            },
            "data": {
                "beers": [
                    {
                        "id": 1,
                        "name": "Yuengling",
                        "brewery": "D. G. Yuengling & Son",
                        "abv": 4.5,
                        "style": "Lager"
                    },
                    {
                        "id": 2,
                        "name": "Leinenkugel's Original",
                        "brewery": "Jacob Leinenkugel Brewing Company",
                        "abv": 4.7,
                        "style": "Pilsner"
                    }
                ]
            }
        },
        {
            "path": "/beers/{id}",
            "name": "beer_by_id",
            "default": {
                "error": True,
                "message": "Not found"
            },
            "data": {
                "reference": {
                    "source": "beers",
                    "find": "beers.id"
                }
            }
        }
    ],
    "other": {
        "test": 1
    }
}


class TestMutableDataResolverBasics:
    def setup_method(self):
        self.resolver = MutableDataResolver(base_data)
    
    def test_get_path_simple(self):
        result = self.resolver.get_data_from_path("routes")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result == base_data.get("routes")

    def test_get_data_resolver_simple(self):
        resolver = self.resolver.get_dynamic_data_resolver("routes")
        assert callable(resolver)
        assert resolver() == base_data.get("routes")

    def test_tokenize_simple_identifier(self):
        identifier = "name=1"
        tokenized_identifier = self.resolver.tokenize_identifier(identifier)
        assert len(tokenized_identifier) == 2
        assert tokenized_identifier[0] == "name"
        assert tokenized_identifier[1] == "1"

    def test_tokenize_identifier_with_multiple_equal_signs(self):
        identifier = "name=test=3"
        tokenized_identifier = self.resolver.tokenize_identifier(identifier)
        assert len(tokenized_identifier) == 2
        assert tokenized_identifier[0] == "name"
        assert tokenized_identifier[1] == "test=3"

    def test_tokenize_data_path(self):
        path = "test.test2.test3"
        tokens = self.resolver.tokenize_data_path(path)
        assert len(tokens) == 3
        assert tokens == ["test", "test2", "test3"]


class TestMutableDataResolverPaths:

    def setup_method(self):
        self.resolver = MutableDataResolver(base_data)
    
    def test_non_existent_path(self):
        pass

class TestMutableDataResolverLists:

    def setup_method(self):
        self.resolver = MutableDataResolver(base_data)
        self.data_list = [{"id": f"{x}", "name": f"Mr. {chr(x)}"} for x in range(10)]

    def test_find_identified_item_in_list(self):
        result = self.resolver.find_identified_item_in_list(self.data_list, "id=1")
        assert result.get("id") == "1"
        assert result.get("name") == f"Mr. {chr(1)}"

    def test_find_identified_item_in_list_mutate(self):
        result = self.resolver.find_identified_item_in_list(self.data_list, "id=1", copy=False)
        result["test"] = "new value"
        assert self.data_list[1].get("test") == "new value"
    
    def test_add_item_to_list(self):
        new_item = {"name", "test_entry"}
        self.resolver.add_item_to_list("routes", new_item)
        result = self.resolver.get_data_from_path("routes")
        assert result[-1] == new_item
    
    def test_add_item_to_non_list(self):
        new_item = {"name", "test_entry"}
        with pytest.raises(ValueError):
            self.resolver.add_item_to_list("other", new_item)
    
    def test_update_item_in_list_existing_field(self):
        update = {"path": 100}
        self.resolver.update_item_in_list("routes", "name=beers", update)
        assert self.resolver.data.get("routes")[0].get("path") == 100
    
    def test_update_item_in_list_new_field(self):
        update = {"anything_else": 100}
        self.resolver.update_item_in_list("routes", "name=beers", update)
        assert self.resolver.data.get("routes")[0].get("anything_else") == 100
