from urllib.parse import parse_qs, urlparse

import pytest
from jobby.templatetags.jobby import paginator_url
from jobby.views import PAGE_VAR


@pytest.mark.parametrize("request_data", [{PAGE_VAR: "2", "foo": "bar"}])
def test_paginator_url(http_request, request_data):
    url = paginator_url(context={"request": http_request}, page_number=1)
    assert parse_qs(urlparse(url).query) == {PAGE_VAR: ["1"], "foo": ["bar"]}
