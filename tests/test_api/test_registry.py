from unittest.mock import Mock, PropertyMock, create_autospec, patch

import pytest
from jobby.apis.base import BaseAPI, SearchResponse
from jobby.apis.registry import APIRegistry, RegistryResponse

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def registry():
    return APIRegistry()


@pytest.fixture
def result_api_one():
    return "Result One"


@pytest.fixture
def result_api_two():
    return "Result Two"


def get_search_response_mock(search_results, status_code, result_count):
    m = create_autospec(SearchResponse)
    type(m).results = PropertyMock(return_value=search_results)
    type(m).status_code = PropertyMock(return_value=status_code)
    type(m).result_count = PropertyMock(return_value=result_count)
    return m


def get_api_mock(search_response_mock, api_name):
    m = create_autospec(BaseAPI)
    m.search.return_value = search_response_mock
    m.name = api_name
    return m


@pytest.fixture
def results_api_one():
    """Search results of API One."""
    return ["foo"]


@pytest.fixture
def results_api_two():
    """Search results of API Two."""
    return ["bar"]


@pytest.fixture
def status_code_api_one():
    """Status code of API One."""
    return 200


@pytest.fixture
def status_code_api_two():
    """Status code of API Two."""
    return 200


@pytest.fixture
def result_count_api_one():
    """Result count of API One."""
    return 101


@pytest.fixture
def result_count_api_two():
    """Result count of API Two."""
    return 99


@pytest.fixture
def response_api_one(results_api_one, status_code_api_one, result_count_api_one):
    """Return a mocked search response for API One."""
    return get_search_response_mock(results_api_one, status_code_api_one, result_count_api_one)


@pytest.fixture
def response_api_two(results_api_two, status_code_api_two, result_count_api_two):
    """Return a mocked search response for API Two."""
    return get_search_response_mock(results_api_two, status_code_api_two, result_count_api_two)


@pytest.fixture
def name_api_one():
    """Return the name for API One."""
    return "API One"


@pytest.fixture
def name_api_two():
    """Return the name for API Two."""
    return "API Two"


@pytest.fixture
def api_one(response_api_one, name_api_one):
    """Create an API Mock 'API One'."""
    return get_api_mock(response_api_one, name_api_one)


@pytest.fixture
def api_two(response_api_two, name_api_two):
    """Create an API Mock 'API Two'."""
    return get_api_mock(response_api_two, name_api_two)


@pytest.fixture
def apis(api_one, api_two):
    return [api_one, api_two]


@pytest.fixture
def set_apis(registry, apis):
    """Add the given APIs to the registry's api list."""
    registry._apis = apis


@pytest.fixture
def register_api(registry, api_one):
    registry.register(api_one)


@pytest.fixture
def unregister_api(registry, api_one):
    registry.unregister(api_one)


@pytest.fixture
def registry_response_mock():
    with patch("jobby.apis.registry.RegistryResponse") as m:
        yield m


class TestAPIRegistry:

    def test_search_filters_none_values(self, registry, api_one, set_apis):
        """
        Assert that ``search`` removes and None values from the search parameters
        before passing them to ``_search``.
        """
        params = {"None": None, "foo": "bar", "bool": False, "number": 0}
        registry.search(**params)
        api_one.search.assert_called_with(**{"foo": "bar", "bool": False, "number": 0})

    def test_register(self, registry, api_one, register_api):
        assert api_one in registry._apis

    def test_register_already_registered(self, registry, api_one, set_apis, register_api):
        assert api_one in registry._apis

    def test_unregister(self, registry, api_one, set_apis, unregister_api):
        assert api_one not in registry._apis

    def test_unregister_not_registered(self, registry, api_one, unregister_api):
        assert api_one not in registry._apis

    @pytest.mark.parametrize("api_one", [Mock()])
    def test_search_api_raises_exception(self, registry, set_apis, api_one, response_api_two, registry_response_mock):
        """Assert that ``search`` ignores exceptions raised by an API."""
        api_one.search.side_effect = Exception
        registry.search(foo="bar")
        registry_response_mock.assert_called_with(response_api_two)

    def test_search_aggregates_results(self, registry, set_apis, results_api_one, results_api_two):
        """Assert that ``search`` returns the results of every response."""
        registry_response = registry.search(foo="bar")
        assert isinstance(registry_response, RegistryResponse)
        assert set(results_api_one).issubset(registry_response.results)
        assert set(results_api_two).issubset(registry_response.results)

    def test_get_details_url(self, registry, set_apis, refnr, name_api_two, api_one, api_two):
        """
        Assert ``get_details_url`` calls the get_details_url method of the API
        with the name that corresponds to the value of Stellenangebot.api.
        """
        registry.get_details_url(name_api_two, refnr)
        api_two.get_details_url.assert_called_with(refnr)
        api_one.get_details_url.assert_not_called()


class TestRegistryResponse:

    @pytest.fixture
    def search_responses(self, response_api_one, response_api_two):
        return response_api_one, response_api_two

    @pytest.fixture
    def registry_response(self, search_responses):
        return RegistryResponse(*search_responses)

    def test_results(self, registry_response, results_api_one, results_api_two):
        """Assert that the results contains the expected items."""
        assert set(results_api_one).issubset(registry_response.results)
        assert set(results_api_two).issubset(registry_response.results)

    @pytest.mark.parametrize("status_code_api_one", [400])
    def test_results_response_not_ok(self, registry_response, results_api_one, results_api_two, status_code_api_one):
        """
        Assert that the results of a response are not included in the results
        if the response status was not ok.
        """
        assert not set(results_api_one).issubset(registry_response.results)
        assert set(results_api_two).issubset(registry_response.results)

    def test_result_count(self, registry_response, result_count_api_one, result_count_api_two):
        """Assert that the result count is the sum of the counts of all responses."""
        assert registry_response.result_count == result_count_api_one + result_count_api_two
