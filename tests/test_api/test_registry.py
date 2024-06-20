from unittest.mock import Mock

import pytest
from jobby.apis.registry import APIRegistry


@pytest.fixture
def registry():
    return APIRegistry()


@pytest.fixture
def api_mock():
    return Mock()


@pytest.fixture(autouse=True)
def set_apis(registry, api_mock):
    registry._apis = [api_mock]


class TestAPIRegistry:

    def test_search_filters_none_values(self, registry, api_mock):
        """
        Assert that ``search`` removes and None values from the search parameters
        before passing them to ``_search``.
        """
        params = {"None": None, "foo": "bar", "bool": False, "number": 0}
        registry.search(**params)
        api_mock.search.assert_called_with(**{"foo": "bar", "bool": False, "number": 0})
