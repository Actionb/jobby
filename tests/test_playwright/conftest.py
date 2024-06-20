import os
import re

import pytest
from django.urls import reverse
from jobby.views import DETAILS_BESCHREIBUNG_ID

# https://github.com/microsoft/playwright-python/issues/439
# https://github.com/microsoft/playwright-pytest/issues/29#issuecomment-731515676
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def session_cookie(client, context):
    """Add a csrftoken cookie."""
    auth_cookie = client.cookies["sessionid"]
    pw_cookie = {
        "name": auth_cookie.key,
        "value": auth_cookie.value,
        "path": auth_cookie["path"],
        "domain": auth_cookie["domain"] or "localhost",
    }
    context.add_cookies([pw_cookie])


@pytest.fixture
def get_url(live_server):
    """Return the URL for a given view name on the current live server."""

    def inner(view_name, **reverse_kwargs):
        return live_server.url + reverse(view_name, **reverse_kwargs)

    return inner


@pytest.fixture
def jobdetails_url():
    return "https://www.arbeitsagentur.de/jobsuche/jobdetail/"


@pytest.fixture
def job_description_text():
    return "Job Description"


@pytest.fixture(autouse=True)
def get_jobdetails_request_mock(requests_mock, jobdetails_url, job_description_text):
    """Provide a mock response for a request to fetch the details page of a job."""
    requests_mock.get(
        re.compile(jobdetails_url),
        text=f"""<p id="{DETAILS_BESCHREIBUNG_ID}"><p>{job_description_text}</p></p>""",
    )


@pytest.fixture
def watchlist_url(get_url):
    return get_url("watchlist")
