import requests

from jobby.models import Stellenangebot, _update_stellenangebot


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

    response = requests.post(
        "https://rest.arbeitsagentur.de/oauth/gettoken_cc",
        headers=headers,
        data=data,
        verify=False,
    )

    return response.json()["access_token"]


def _search(**params):  # pragma: no cover
    """
    Search for jobs.

    Params can be found here: https://jobsuche.api.bund.dev/
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


def _parse_arbeitsort(arbeitsort_dict):
    """
    Return a string for the 'arbeitsort' field from the given data from a
    search result.
    """
    # TODO: include data like PLZ or distance into the string
    try:
        return arbeitsort_dict["ort"]
    except KeyError:
        return ""


def _process_results(results):
    """
    Walk through the dictionaries of the search results and return them as
    Stellenangebot instances.
    """
    # TODO: include "externeUrl" data that is present on some results
    processed = []
    for result in results:
        instance = Stellenangebot(
            titel=result.get("titel", ""),
            refnr=result.get("refnr", ""),
            beruf=result.get("beruf", ""),
            arbeitgeber=result.get("arbeitgeber", ""),
            arbeitsort=_parse_arbeitsort(result.get("arbeitsort", {})),
            # TODO: parse into date and datetime:
            eintrittsdatum=result.get("eintrittsdatum", ""),
            veroeffentlicht=result.get("aktuelleVeroeffentlichungsdatum", ""),
            modified=result.get("modifikationsTimestamp", ""),
        )
        processed.append(instance)
    return processed


def _get_existing(refs):
    return Stellenangebot.objects.filter(refnr__in=refs)


def search(**params):
    try:
        response = _search(**{k: v for k, v in params.items() if v is not None})
    except Exception:
        # TODO: error handling
        raise
    if response.status_code == 200:
        data = response.json()
        if not data.get("maxErgebnisse", 0):
            return []

        # Parse each search result, and collect the ref numbers for database
        # lookups.
        angebote = _process_results(data["stellenangebote"])
        refs = set(s.refnr for s in angebote)

        # Create the list of Stellenangebot instances.
        # Use saved Stellenangebot instances whenever possible. Update
        # saved instances if the data has changed.
        results = []
        existing = _get_existing(refs)
        for angebot in angebote:
            if angebot.refnr in existing.values_list("refnr", flat=True):
                stellenangebot = existing.get(refnr=angebot.refnr)
                _update_stellenangebot(stellenangebot, angebot)
            else:
                stellenangebot = angebot
            results.append(stellenangebot)
        return results
    else:
        # TODO: handle a bad response
        return []
