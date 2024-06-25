from jobby.apis.base import BaseAPI
from jobby.apis.registry import registry


def register(api_cls: type(BaseAPI)):
    """Register the given API endpoint implementation with the registry."""
    assert issubclass(api_cls, BaseAPI)
    registry.register(api_cls())
    return api_cls
