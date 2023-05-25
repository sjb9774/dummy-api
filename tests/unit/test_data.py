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

