from unittest.mock import Mock, patch

import pytest
import requests
from jobby.models import Stellenangebot
from jobby.search import _parse_arbeitsort, _process_results, search

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def search_result(refnr):
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
    return [search_result]


@pytest.fixture
def response_status_code():
    return requests.codes["ok"]


@pytest.fixture
def response_data(search_results):
    return {
        "maxErgebnisse": len(search_results),
        "stellenangebote": search_results,
    }


@pytest.fixture()
def response_mock(response_status_code, response_data):
    r = Mock()
    r.status_code = response_status_code
    r.json.return_value = response_data
    return r


@pytest.fixture
def search_mock(response_mock):
    with patch("jobby.search._search") as m:
        m.return_value = response_mock
        yield m


def test_search(search_mock):
    angebote = search()
    assert len(angebote) == 1
    assert isinstance(angebote[0], Stellenangebot)
    assert angebote[0].titel == "Software Entwickler"


@pytest.mark.parametrize("response_status_code", [requests.codes["bad_request"]])
def test_search_bad_request(search_mock, response_status_code):
    # TODO: test against an actual sentinel value for bad requests?
    assert search() == []


@pytest.mark.parametrize("search_results", [[]])
def test_search_no_results(search_mock, search_results):
    assert search() == []


def test_search_filters_none_values(search_mock):
    """
    Assert that search removes and None values from the search parameters
    before passing them to _search.
    """
    params = {"None": None, "foo": "bar", "bool": False, "number": 0}
    search(**params)
    search_mock.assert_called_with(**{"foo": "bar", "bool": False, "number": 0})


def test_checks_for_existing(search_mock, stellenangebot, refnr, search_result):
    with patch("jobby.search._get_existing") as existing_mock:
        search()
    existing_mock.assert_called_with({refnr})


def test_updates_existing(search_mock, stellenangebot):
    with patch("jobby.search._update_stellenangebot") as update_mock:
        search()
        update_mock.assert_called()


@pytest.mark.parametrize(
    "ort_data, expected",
    [
        ({"ort": "Dortmund"}, "Dortmund"),
        # TODO: enable these tests once _parse_arbeitsort has been improved:
        # ({"ort": "Dortmund", "plz": "44263"}, "Dortmund, 44263"),
        # ({"ort": "Dortmund", "plz": "44263", "region": "NRW"}, "Dortmund, 44263 (NRW)"),  # noqa
    ],
)
def test_parse_arbeitsort(ort_data, expected):
    assert _parse_arbeitsort(ort_data) == expected


def test_process_results():
    search_result = {
        "titel": "Software Developer",
        "refnr": "789-456-0123",
        "beruf": "Informatiker",
        "arbeitgeber": "IHK Dortmund",
        "arbeitsort": {"ort": "Dortmund", "plz": "44263", "region": "NRW"},
        "eintrittsdatum": "2024-07-01",
        "aktuelleVeroeffentlichungsdatum": "2024-05-30",
        "modifikationsTimestamp": "2024-05-22T09:00:15.099",
    }
    with patch("jobby.search._parse_arbeitsort", new=Mock(return_value="mocked")) as arbeitsort_mock:
        results = _process_results([search_result])
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, Stellenangebot)
        assert result.titel == search_result["titel"]
        assert result.refnr == search_result["refnr"]
        assert result.beruf == search_result["beruf"]
        assert result.arbeitgeber == search_result["arbeitgeber"]
        arbeitsort_mock.assert_called_with(search_result["arbeitsort"])
        assert result.eintrittsdatum == search_result["eintrittsdatum"]
        assert result.veroeffentlicht == search_result["aktuelleVeroeffentlichungsdatum"]
        assert result.modified == search_result["modifikationsTimestamp"]
