from datetime import datetime
from unittest.mock import create_autospec

import pytest
from jobby.apis.base import BaseAPI, SearchResponse
from jobby.models import Stellenangebot

pytestmark = [pytest.mark.django_db]


class DummyResponse(SearchResponse):
    def _get_results(self, data) -> list[Stellenangebot]:
        pass

    def _get_total_result_count(self, data) -> int:
        pass


@pytest.fixture
def api_mock():
    m = create_autospec(BaseAPI)
    m.name = "Mocked API"
    return m


@pytest.fixture
def search_response(response_mock, api_mock):
    return DummyResponse(response_mock, api_mock)


class TestSearchResponse:

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

    def test_set_api_on_results_api_not_set(self, search_response, stellenangebot, api_mock):
        """
        Assert that ``_set_api_on_results`` sets the api field on the results
        if that field is not set.
        """
        stellenangebot.api = ""
        results = search_response._set_api_on_results([stellenangebot])
        assert results[0].api == api_mock.name

    def test_set_api_on_results_api_already_set(self, search_response, stellenangebot, api_mock):
        """
        Assert that ``_set_api_on_results`` does not change the api field on the
        results if that field is already set.
        """
        results = search_response._set_api_on_results([stellenangebot])
        assert results[0].api == stellenangebot.api
