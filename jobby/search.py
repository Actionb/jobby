from datetime import datetime
from functools import cached_property

import requests
from django.conf import settings
from django.utils.timezone import make_aware

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
    # TODO: what is "pav"?
    params.setdefault("pav", "false")
    # TODO: is this angebotsart required?
    params.setdefault("angebotsart", "1")

    # FIXME: queries that include these parameters never return results, so
    #  ignore them for now:
    params.pop("behinderung", None)
    params.pop("corona", None)

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


def search(**params):
    response = _search(**{k: v for k, v in params.items() if v is not None})
    return SearchResponse(response)


class SearchResponse:

    def __init__(self, response):
        self.response = response
        self.data = response.json()

    @property
    def status_code(self):  # pragma: no cover
        return self.response.status_code

    @cached_property
    def results(self):  # pragma: no cover
        return self._get_results(self.data)

    @property
    def result_count(self):  # pragma: no cover
        return self._get_total_result_count(self.data)

    @property
    def has_results(self):
        # FIXME: some queries return responses without "stellenangebote" data
        #  (f.ex. Angebotsart=Ausbildung)
        return self._get_total_result_count(self.data) > 0 and "stellenangebote" in self.data

    def _get_results(self, data):
        if not self.has_results:
            return []

        # Parse each search result, and collect the ref numbers for database
        # lookups.
        angebote = self._process_results(data["stellenangebote"])
        refs = set(s.refnr for s in angebote)

        # Create the list of Stellenangebot instances.
        # Use saved Stellenangebot instances whenever possible. Update
        # saved instances if the data has changed.
        results = []
        existing = self._get_existing(refs)
        existing_refs = set(existing.values_list("refnr", flat=True))
        for angebot in angebote:
            if angebot.refnr in existing_refs:
                stellenangebot = existing.get(refnr=angebot.refnr)
                _update_stellenangebot(stellenangebot, angebot)
            else:
                stellenangebot = angebot
            results.append(stellenangebot)
        return results

    def _process_results(self, results):
        """
        Walk through the dictionaries of search results and return them as
        Stellenangebot instances.
        """
        # TODO: include "externeUrl" data that is present on some results
        processed = []
        # TODO: use SearchResultForm here?
        for result in results:
            instance = Stellenangebot(
                titel=result.get("titel", ""),
                refnr=result.get("refnr", ""),
                beruf=result.get("beruf", ""),
                arbeitgeber=result.get("arbeitgeber", ""),
                arbeitsort=self._parse_arbeitsort(result.get("arbeitsort", {})),
                # TODO: parse into date and datetime:
                eintrittsdatum=result.get("eintrittsdatum", ""),
                veroeffentlicht=result.get("aktuelleVeroeffentlichungsdatum", ""),
                modified=self._make_aware(result.get("modifikationsTimestamp", "")),
                externe_url=result.get("externeUrl", ""),
            )
            processed.append(instance)
        return processed

    @staticmethod
    def _parse_arbeitsort(arbeitsort_dict):
        """
        Return a string for the 'arbeitsort' field from the given data from a
        search result.
        """
        ort = arbeitsort_dict.get("ort", "")
        plz = arbeitsort_dict.get("plz", "")
        if plz:
            return f"{ort}, {plz}"
        else:
            return ort

    @staticmethod
    def _make_aware(datetime_string):
        """Return a timezone-aware datetime instance from the given string."""
        try:
            return make_aware(datetime.fromisoformat(datetime_string))
        except ValueError:
            return ""

    @staticmethod
    def _get_existing(refs):
        return Stellenangebot.objects.filter(refnr__in=refs)

    @staticmethod
    def _get_total_result_count(data):
        return data.get("maxErgebnisse", 0)
