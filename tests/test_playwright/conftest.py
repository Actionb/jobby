import os

import pytest
from django.urls import reverse

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
