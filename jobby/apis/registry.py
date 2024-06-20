class APIRegistry:

    def __init__(self):
        self._apis = []

    def register(self, api):
        if api not in self._apis:
            self._apis.append(api)

    def unregister(self, api):
        if api in self._apis:
            self._apis.remove(api)

    def search(self, **params):
        for api in self._apis:
            # TODO: merge search results of the apis instead of just returning
            #  the results of the first api
            return api.search(**{k: v for k, v in params.items() if v is not None})


registry = APIRegistry()


def register(api_cls):
    from jobby.apis.base import BaseAPI

    assert issubclass(api_cls, BaseAPI)
    # TODO: how to instantiate the apis?
    registry.register(api_cls())
    return api_cls
