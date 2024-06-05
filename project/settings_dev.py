from .settings import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [".localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Required for debug_toolbar:
INTERNAL_IPS = ["127.0.0.1"]
