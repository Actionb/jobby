from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property

from django.utils.timezone import make_aware

from jobby.models import Stellenangebot, _update_stellenangebot


class BaseAPI(ABC):

    @abstractmethod
    def search(self) -> "SearchResponse": ...


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
