from datetime import datetime
from unittest.mock import Mock, PropertyMock, patch

# noinspection PyPackageRequirements
import pytest
import requests
from jobby.apis.bundesagentur_api import BundesagenturAPI, BundesagenturResponse
from jobby.models import Stellenangebot

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def search_result(refnr):
    """Return a single search result in the form of a dictionary."""
    return {
        "titel": "Software Entwickler",
        "refnr": refnr,
        "beruf": "Informatiker",
        "arbeitgeber": "IHK Dortmund",
        "arbeitsort": {"ort": "Dortmund", "plz": "44263", "region": "NRW"},
        "eintrittsdatum": "2024-07-01",
        "aktuelleVeroeffentlichungsdatum": "2024-05-30",
        "modifikationsTimestamp": "2024-05-22T09:00:15.099",
        "kundennummerHash": "a78er879s124mre",
        "externeUrl": "www.google.de",
    }


@pytest.fixture
def search_results(search_result):
    """Return the list of search results."""
    return [search_result]


@pytest.fixture
def response_status_code():
    """Return the status code of a response."""
    return requests.codes["ok"]


@pytest.fixture
def response_data(search_results):
    """Return the data of a response."""
    return {
        "maxErgebnisse": len(search_results),
        "stellenangebote": search_results,
    }


@pytest.fixture()
def response_mock(response_status_code, response_data):
    """Return a mocked response with the given status code and data."""
    r = Mock()
    r.status_code = response_status_code
    r.json.return_value = response_data
    return r


@pytest.fixture
def search_mock(response_mock, api):
    """
    Mock the ``_search`` function method to return the given response instead
    of making outgoing requests.
    """
    with patch.object(api, "_search") as m:
        m.return_value = response_mock
        yield m


@pytest.fixture
def search_response(response_mock):
    """Return a SearchResponse instance with the given response."""
    return BundesagenturResponse(response_mock)


@pytest.fixture
def api():
    return BundesagenturAPI()


class TestBundesagenturAPI:

    def test_search_returns_search_response(self, search_mock, api):
        """Assert that ``search`` returns a SearchResponse instance."""
        assert isinstance(api.search(), BundesagenturResponse)


class TestSearchResponse:

    def test_get_results(self, search_response):
        """
        Assert that ``_get_results`` returns the expected Stellenangebot
        instances.
        """
        results = search_response._get_results(search_response.data)
        assert len(results) == 1
        assert isinstance(results[0], Stellenangebot)
        assert results[0].titel == "Software Entwickler"

    @pytest.mark.parametrize("search_results", [[1]])
    def test_has_results(self, search_response, search_results):
        """
        Assert that ``has_results`` returns True if the search request returned
        results.
        """
        assert search_response.has_results

    @pytest.mark.parametrize("search_results", [[]])
    def test_has_results_no_results(self, search_response, search_results):
        """
        Assert that ``has_results`` returns False if the search did not return
        any results.
        """
        assert not search_response.has_results

    @pytest.mark.parametrize("response_data", [{"maxErgebnisse": 1}])
    def test_has_results_no_stellenangebote(self, search_response, response_data):
        """
        Assert that ``has_results`` returns False if the response data does not
        contain a 'stellenangebote' key.
        """
        # For some query parameters the API returns responses without the
        # 'stellenangebote' key. (this may have been a temporary API bug?)
        assert not search_response.has_results

    def test_get_results_no_results(self, search_response):
        """
        Assert that ``_get_results`` returns an empty list if the search did
        not return results (implied by ``has_results`` returning False).
        """
        with patch(
            "jobby.apis.bundesagentur_api.BundesagenturResponse.has_results", new=PropertyMock(return_value=False)
        ):
            assert search_response._get_results(search_response.data) == []

    def test_get_results_updates_existing(self, search_response, stellenangebot):
        """
        Assert that ``_get_results`` calls the function that updates existing
        Stellenangebot instances.
        """
        with patch("jobby.apis.bundesagentur_api._update_stellenangebot") as update_mock:
            search_response._get_results(search_response.data)
        update_mock.assert_called()

    def test_process_results(self, search_response):
        """
        Assert that ``_process_results`` returns the expected Stellenangebot
        instances.
        """
        search_result = {
            "titel": "Software Developer",
            "refnr": "789-456-0123",
            "beruf": "Informatiker",
            "arbeitgeber": "IHK Dortmund",
            "arbeitsort": {"ort": "Dortmund", "plz": "44263", "region": "NRW"},
            "eintrittsdatum": "2024-07-01",
            "aktuelleVeroeffentlichungsdatum": "2024-05-30",
            "modifikationsTimestamp": "2024-05-22T09:00:15.099",
            "externeUrl": "www.foobar.com",
        }
        with patch.object(search_response, "_parse_arbeitsort", new=Mock(return_value="mocked")) as arbeitsort_mock:
            with patch.object(search_response, "_make_aware", new=Mock(return_value="2024-06-06")) as make_aware_mock:
                results = search_response._process_results([search_result])
                assert len(results) == 1
                result = results[0]
                assert isinstance(result, Stellenangebot)
                assert result.titel == search_result["titel"]
                assert result.refnr == search_result["refnr"]
                assert result.beruf == search_result["beruf"]
                assert result.arbeitgeber == search_result["arbeitgeber"]
                assert result.arbeitsort == "mocked"
                arbeitsort_mock.assert_called_with(search_result["arbeitsort"])
                assert result.eintrittsdatum == search_result["eintrittsdatum"]
                assert result.veroeffentlicht == search_result["aktuelleVeroeffentlichungsdatum"]
                assert result.modified == "2024-06-06"
                make_aware_mock.assert_called_with(search_result["modifikationsTimestamp"])
                assert result.externe_url == "www.foobar.com"

    @pytest.mark.parametrize(
        "ort_data, expected",
        [
            ({}, ""),
            ({"ort": "Dortmund"}, "Dortmund"),
            ({"ort": "Dortmund", "plz": "44263"}, "Dortmund, 44263"),
        ],
    )
    def test_parse_arbeitsort(self, search_response, ort_data, expected):
        """Assert that ``_parse_arbeitsort`` returns the expected strings."""
        assert search_response._parse_arbeitsort(ort_data) == expected

    def test_make_aware(self, search_response):
        """
        Assert that ``_make_aware`` returns the expected timezone-aware
        datetime object.
        """
        dt = search_response._make_aware("2024-05-22T09:00:15.099")
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None

    def test_make_aware_invalid_datetime(self, search_response):
        """
        Assert that ``_make_aware`` returns an empty string if the
        datetime_string argument is not a valid datetime.
        """
        assert search_response._make_aware("") == ""
