from unittest.mock import Mock

import pytest
import requests

################################################################################
# BaseAPI & SearchResponse
################################################################################


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
