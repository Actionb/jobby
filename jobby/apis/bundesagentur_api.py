import requests
from django.conf import settings

from jobby.apis.base import BaseAPI, SearchResponse
from jobby.apis.registry import register


def get_jwt():  # pragma: no cover
    """Fetch the jwt token object."""
    headers = {
        "User-Agent": "Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4",
        "Host": "rest.arbeitsagentur.de",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }

    data = {
        "client_id": "c003a37f-024f-462a-b36d-b001be4cd24a",
        "client_secret": "32a39620-32b3-4307-9aa1-511e3d7f48a8",
        "grant_type": "client_credentials",
    }

    kwargs = {
        "url": "https://rest.arbeitsagentur.de/oauth/gettoken_cc",
        "headers": headers,
        "data": data,
    }
    if settings.DEBUG:
        # Do not verify certificates during development:
        kwargs["verify"] = False
    response = requests.post(**kwargs)
    return response.json()["access_token"]


def _search(**params):  # pragma: no cover
    """
    Search for jobs.

    Params can be found here: https://jobsuche.api.bund.dev/
    """
    # TODO: The API supports an undocumented "pav" parameter that affects
    #  results. What is that? "Private Arbeitsvermittler"?
    # params.setdefault("pav", "false")

    headers = {
        "User-Agent": "Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4",
        "Host": "rest.arbeitsagentur.de",
        "OAuthAccessToken": get_jwt(),
        "Connection": "keep-alive",
    }

    kwargs = {
        "url": "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs",
        "headers": headers,
        "params": params,
    }
    if settings.DEBUG:
        # Do not verify certificates during development:
        kwargs["verify"] = False
    return requests.get(**kwargs)


@register
class BundesagenturAPI(BaseAPI):

    def search(self, **params):
        response = _search(**params)
        # TODO: check response status code
        return SearchResponse(response)
