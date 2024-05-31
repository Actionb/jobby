from unittest.mock import Mock, patch

import pytest
import requests
from jobby.models import Stellenangebot
from jobby.query import search

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def refnr():
    return "789-456-1230"


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
    with patch("jobby.query._search") as m:
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


def test_search_search_exception(search_mock):
    # TODO: implement error handling and test it here
    search_mock.side_effect = Exception()
    with pytest.raises(Exception):
        search()


def test_search_filters_none_values(search_mock):
    """
    Assert that search removes and None values from the search parameters
    before passing them to _search.
    """
    params = {"None": None, "foo": "bar", "bool": False, "number": 0}
    search(**params)
    search_mock.assert_called_with(**{"foo": "bar", "bool": False, "number": 0})


@pytest.fixture
def stellenangebot(refnr):
    return StellenangebotFactory(
        titel="Software Developer",
        refnr=refnr,
        beruf="Informatiker",
        arbeitgeber="IHK Dortmund",
        arbeitsort={"ort": "Dortmund", "plz": "44263", "region": "NRW"},
        eintrittsdatum="2024-07-01",
        veroeffentlicht="2024-05-30",
        modified="2024-05-22T09:00:15.099",
    )


def test_checks_for_existing(search_mock, stellenangebot, refnr, search_result):
    filter_mock = Mock()
    filter_mock.return_value.values_list.return_value = []
    with patch.object(Stellenangebot, "objects") as queryset_mock:
        queryset_mock.filter = filter_mock
        search()
        filter_mock.assert_called_with(refnr__in={refnr})


def test_updates_existing(search_mock, stellenangebot):
    search()
    stellenangebot.refresh_from_db()
    assert stellenangebot.titel == "Software Entwickler"
    assert stellenangebot.beruf == "Informatiker"
