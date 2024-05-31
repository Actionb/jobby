import dataclasses

import requests

from jobby.models import Stellenangebot


# noinspection SpellCheckingInspection
@dataclasses.dataclass
class SearchResult:
    titel: str
    refnr: str
    beruf: str = ""
    arbeitgeber: str = ""
    arbeitsort: dict = dataclasses.field(default_factory=dict)
    eintrittsdatum: str = ""
    aktuelleVeroeffentlichungsdatum: str = ""
    modifikationsTimestamp: str = ""
    kundennummerHash: str = ""  # TODO: this field does not exist on Stellenangebot model
    externeUrl: str = ""  # TODO: this field does not exist on Stellenangebot model

    @property
    def arbeitsort_string(self):
        arbeitsort = self.arbeitsort.get("ort", "")
        plz = self.arbeitsort.get("plz", "")
        region = self.arbeitsort.get("region", "")
        if arbeitsort and plz:
            arbeitsort = f"{arbeitsort}, {plz}"
        if region:
            if arbeitsort:
                arbeitsort = f"{arbeitsort} ({region})"
            else:
                arbeitsort = region
        return arbeitsort.strip()

    @property
    def stellenangebot(self):
        """Return a Stellenangebot instance for this search result."""
        return Stellenangebot(
            titel=self.titel,
            refnr=self.refnr,
            beruf=self.beruf,
            arbeitgeber=self.arbeitgeber,
            arbeitsort=self.arbeitsort_string,
            eintrittsdatum=self.eintrittsdatum,
            veroeffentlicht=self.aktuelleVeroeffentlichungsdatum,
            modified=self.modifikationsTimestamp,
        )


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
        refs = set()
        angebote = []
        for r in data["stellenangebote"]:
            angebot = SearchResult(**r)
            refs.add(angebot.refnr)
            angebote.append(angebot)

        # Create the list of Stellenangebot instances.
        # Use saved Stellenangebot instances whenever possible. Update
        # saved instances if the data has changed.
        results = []
        # TODO: extract existing into a separate method for easier testing
        existing = Stellenangebot.objects.filter(refnr__in=refs)
        for angebot in angebote:
            if angebot.refnr in existing.values_list("refnr", flat=True):
                stellenangebot = existing.get(refnr=angebot.refnr)
                update_dict = {}
                for k, v in dataclasses.asdict(angebot).items():
                    # FIXME: angebot.fields do not match the Stellenangebot model fields
                    if getattr(stellenangebot, k) != v:
                        update_dict[k] = v
                        setattr(stellenangebot, k, v)
                if update_dict:
                    existing.filter(refnr=angebot.refnr).update(**update_dict)
            else:
                stellenangebot = angebot.stellenangebot
            results.append(stellenangebot)
        return results
    else:
        # TODO: handle a bad response
        return []
