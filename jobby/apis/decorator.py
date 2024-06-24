from jobby.apis.base import BaseAPI
from jobby.apis.registry import registry


def register(api_cls: type(BaseAPI)):
    assert issubclass(api_cls, BaseAPI)
    # TODO: how to instantiate the apis?
    registry.register(api_cls())
    return api_cls
