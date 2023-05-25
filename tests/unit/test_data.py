import pytest
from dummy_api.data import MutableDataStore

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


class TestMutableDataStoreResolvers:

    def setup_method(self):
        self.store = MutableDataStore()

    def test_add_group_then_get_resolver(self):
        self.store.add_data_group("data", {"value": 100})
        resolver = self.store.build_data_resolver("data")
        assert resolver() == {"value": 100}

    def test_get_resolver_then_add_group(self):
        resolver = self.store.build_data_resolver("data")
        self.store.add_data_group("data", {"value": 100})
        assert resolver() == {"value": 100}

    def test_resolver_with_query_path_no_params(self):
        self.store.add_data_group("data", {"root": {"value": 200}})
        resolver = self.store.build_data_resolver("data", "root.value")
        assert resolver() == 200

    def test_resolver_with_query_path_with_static_param(self):
        self.store.add_data_group(
            "data",
            {"root": {"items": [{"id": 1, "name": "Stephen"}, {"id": 2, "name": "Savannah"}]}}
        )
        resolver = self.store.build_data_resolver("data", "root.items[id=1].name")
        assert resolver() == "Stephen"

    def test_resolver_with_query_path_with_dynamic_param(self):
        self.store.add_data_group(
            "data",
            {"root": {"items": [{"id": 1, "name": "Stephen"}, {"id": 2, "name": "Savannah"}]}}
        )
        resolver = self.store.build_data_resolver("data", "root.items[id={id}].name")
        assert resolver(id=2) == "Savannah"

    def test_resolver_with_unhandled_query_path(self):
        self.store.add_data_group("data", {"name": "Stephen"})
        resolver = self.store.build_data_resolver("data", "incorrect.path")
        assert resolver() is None

    def test_resolver_with_incorrect_dynamic_params(self):
        self.store.add_data_group(
            "data",
            {"root": {"items": [{"id": 1, "name": "Stephen"}, {"id": 2, "name": "Savannah"}]}}
        )
        resolver = self.store.build_data_resolver("data", "root.items[id={id}]")
        with pytest.raises(ValueError):
            resolver(nonexistent_param=2)

    def test_resolver_without_passing_dynamic_params(self):
        self.store.add_data_group(
            "data",
            {"root": {"items": [{"id": 1, "name": "Stephen"}, {"id": 2, "name": "Savannah"}]}}
        )
        resolver = self.store.build_data_resolver("data", "root.items[id={id}]")
        with pytest.raises(ValueError):
            resolver()

    def test_build_resolver_with_data_group_no_query_path(self):
        group_data = {"data": 1}
        resolver = self.store.build_resolver_for_data_group("data", group_data)
        assert resolver() == {"data": 1}

    def test_build_resolver_get_resolver(self):
        group_data = {"data": 1}
        resolver = self.store.build_resolver_for_data_group("data", group_data)
        fetched_resolver = self.store.get_resolver_by_name("data")
        assert resolver == fetched_resolver
        assert resolver() == fetched_resolver()
