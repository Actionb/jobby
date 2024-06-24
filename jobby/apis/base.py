from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property

from django.utils.timezone import make_aware
from requests import Response

from jobby.models import Stellenangebot


class BaseAPI(ABC):

    @abstractmethod
    def search(self, **params) -> "SearchResponse":
        """Call the API with the given search parameters."""


class SearchResponse(ABC):

    def __init__(self, response: Response):
        self.response: Response = response
        self.data: dict = response.json()

    @property
    def status_code(self) -> int:  # pragma: no cover
        return self.response.status_code

    @cached_property
    def results(self) -> list[Stellenangebot]:  # pragma: no cover
        return self._get_results(self.data)

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
