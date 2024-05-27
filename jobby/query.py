import dataclasses

import requests


@dataclasses.dataclass
class Result:
    titel: str


def get_jwt():
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

    response = requests.post(
        "https://rest.arbeitsagentur.de/oauth/gettoken_cc",
        headers=headers,
        data=data,
        verify=False,
    )

    return response.json()["access_token"]


def _search(**params):
    """
    Search for jobs.

    Prams can be found here: https://jobsuche.api.bund.dev/
    """
    # just for testing:
    default_params = (
        ("angebotsart", "1"),
        ("page", "1"),
        ("pav", "false"),
        ("size", "100"),
        ("umkreis", "25"),
        ("was", params.get("was", "Software")),
        ("wo", params.get("wo", "Dortmund")),
    )

    # FIXME: a request using these params does not return results, although
    #  the params contain the same data as the default_params

    # # TODO: set defaults on model
    params.setdefault("page", "1")
    params.setdefault("size", "100")
    params.setdefault("umkreis", "25")
    # TODO: what is "pav"?
    params.setdefault("pav", "false")
    # TODO: is this angebotsart required?
    params.setdefault("angebotsart", "1")

    headers = {
        "User-Agent": "Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4",
        "Host": "rest.arbeitsagentur.de",
        "OAuthAccessToken": get_jwt(),
        "Connection": "keep-alive",
    }

    response = requests.get(
        "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs",
        headers=headers,
        params=default_params,
        verify=False,
    )
    return response


def query(**kwargs):
    try:
        response = _search(**{k: v for k, v in kwargs.items() if v is not None})
        if response.status_code == 200:
            results = response.json()
            if results.get("maxErgebnisse", 0):
                return [Result(r["titel"]) for r in results["stellenangebote"]]
            else:
                return []
        else:
            return [Result(f"Bad response: {response.status_code}")]
    except Exception:
        # TODO: error handling
        raise
