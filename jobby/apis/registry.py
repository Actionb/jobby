from functools import cached_property

import requests

from jobby.apis.base import BaseAPI, SearchResponse
from jobby.models import Stellenangebot


class RegistryResponse:

    def __init__(self, *search_responses: SearchResponse):
        self.search_responses = search_responses

    @property
    def has_results(self) -> bool:  # pragma: no cover
        return self.result_count > 0

    @cached_property
    def result_count(self) -> int:
        return sum(r.result_count for r in self.search_responses)

    @cached_property
    def results(self) -> list[Stellenangebot]:
        results = []
        for search_response in self.search_responses:
            if search_response.status_code != requests.codes.ok:
                continue
            results.extend(search_response.results)
        return results


class APIRegistry:

    def __init__(self):
        self._apis: list[BaseAPI] = []

    def register(self, api: "BaseAPI"):
        """Register an API with this registry."""
        if api not in self._apis:
            self._apis.append(api)

    def unregister(self, api: "BaseAPI"):
        """Unregister an API from this registry."""
        if api in self._apis:
            self._apis.remove(api)

    def search(self, **params) -> RegistryResponse:
        """
        Call the search method of each registered API and return the aggregate
        results.
        """
        search_responses = []
        for api in self._apis:
            try:
                api_response = api.search(**{k: v for k, v in params.items() if v is not None})
            except Exception:  # noqa
                continue
            search_responses.append(api_response)
        return RegistryResponse(*search_responses)

    def get_details_url(self, api_name, refnr):
        """Return the URL to the details page for the given API and refnr."""
        for api in self._apis:
            if api.name == api_name:
                return api.get_details_url(refnr)
        else:  # pragma: no cover
            return ""


registry = APIRegistry()
