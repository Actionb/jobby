# https://github.com/bundesAPI/jobsuche-api/blob/main/api_example.py
import pprint

import requests


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
        "https://rest.arbeitsagentur.de/oauth/gettoken_cc", headers=headers, data=data, verify=False
    )

    return response.json()


def search(jwt, what, where):
    """
    Search for jobs.

    Prams can be found here: https://jobsuche.api.bund.dev/
    """
    params = (
        ("angebotsart", 1),
        ("page", "1"),
        ("pav", "false"),
        ("size", "100"),
        ("umkreis", "25"),
        ("was", what),
        ("wo", where),
    )

    headers = {
        "User-Agent": "Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4",
        "Host": "rest.arbeitsagentur.de",
        "OAuthAccessToken": jwt,
        "Connection": "keep-alive",
    }

    response = requests.get(
        "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs",
        headers=headers,
        params=params,
        verify=False,
    )
    return response.json()


if __name__ == "__main__":
    jwt = get_jwt()
    result = search(jwt["access_token"], "Software", "Dortmund")
    with open("stellenangebote.json", "w") as f:
        pprint.pprint(result["stellenangebote"], stream=f)
