from urllib.parse import parse_qs, urlparse

# noinspection PyPackageRequirements
import pytest
from django.http import HttpResponse, QueryDict
from django.urls import path, reverse
from django.utils.http import urlencode
from jobby.templatetags.jobby import add_search_filters, paginator_url
from jobby.views import PAGE_VAR


@pytest.mark.parametrize("request_data", [{PAGE_VAR: "2", "foo": "bar"}])
def test_paginator_url(get_request, request_data):
    """Assert that ``paginator_url`` returns the expected URL."""
    url = paginator_url(context={"request": get_request}, page_number=1)
    assert parse_qs(urlparse(url).query) == {PAGE_VAR: ["1"], "foo": ["bar"]}


def get_query_params(url):
    """Return a dictionary of the query string parameters in the given URL."""
    return QueryDict(urlparse(url).query)


urlpatterns = [
    path("suche/", lambda r: HttpResponse(), name="suche"),
    path("not_suche/", lambda r: HttpResponse(), name="not_suche"),
]


@pytest.fixture
def add_search_params_context():
    return {"preserved_search_filters": urlencode({"_search_filters": urlencode([("was", "Foo"), ("wo", "Bar")])})}


@pytest.mark.urls(__name__)
def test_add_search_params_url_not_for_search_page(add_search_params_context):
    """
    Assert that the preserved search filters are added to the query string
    under a special parameter if the url is not for the search page.
    """
    url = add_search_filters(add_search_params_context, reverse("not_suche"))
    params = get_query_params(url)
    assert params["_search_filters"] == "was=Foo&wo=Bar"


@pytest.mark.urls(__name__)
def test_add_search_params_url_for_search_page(add_search_params_context):
    """
    Assert that the preserved search filters are added to the query string
    directly if the url is for the search page.
    """
    url = add_search_filters(add_search_params_context, reverse("suche"))
    params = get_query_params(url)
    assert params["was"] == "Foo"
    assert params["wo"] == "Bar"
