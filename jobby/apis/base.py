from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property

from django.utils.timezone import make_aware
from requests import Response

from jobby.models import Stellenangebot


class BaseAPI(ABC):
    name: str

    def __init__(self):
        if not self.name:
            self.name = str(self.__class__)

    @abstractmethod
    def search(self, **params) -> "SearchResponse":
        """Call the API with the given search parameters."""


class SearchResponse(ABC):

    def __init__(self, response: Response, api: BaseAPI):
        self.response: Response = response
        self.data: dict = response.json()
        self.api = api

    @property
    def status_code(self) -> int:  # pragma: no cover
        return self.response.status_code

    @cached_property
    def results(self) -> list[Stellenangebot]:  # pragma: no cover
        return self._set_api_on_results(self._get_results(self.data))

    @property
    def result_count(self) -> int:  # pragma: no cover
        return self._get_total_result_count(self.data)

    @property
    def has_results(self) -> bool:
        return self._get_total_result_count(self.data) > 0

    @abstractmethod
    def _get_total_result_count(self, data) -> int: ...

    @abstractmethod
    def _get_results(self, data) -> list[Stellenangebot]: ...

    @staticmethod
    def _make_aware(datetime_string: str) -> datetime | str:
        """Return a timezone-aware datetime instance from the given string."""
        try:
            return make_aware(datetime.fromisoformat(datetime_string))
        except ValueError:
            return ""

    def _set_api_on_results(self, results: list[Stellenangebot]) -> list[Stellenangebot]:
        """Set the value for Stellenangebot.api field on each result."""
        for result in results:
            if not result.api:
                result.api = self.api.name
        return results
