from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property

from django.utils.timezone import make_aware


class BaseAPI(ABC):

    @abstractmethod
    def search(self) -> "SearchResponse": ...


class SearchResponse(ABC):

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
        return self._get_total_result_count(self.data) > 0

    @abstractmethod
    def _get_total_result_count(self, data) -> int: ...

    @abstractmethod
    def _get_results(self, data) -> list: ...

    @staticmethod
    def _make_aware(datetime_string):
        """Return a timezone-aware datetime instance from the given string."""
        try:
            return make_aware(datetime.fromisoformat(datetime_string))
        except ValueError:
            return ""
