import getpass
from pathlib import Path

from .base import *  # noqa

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "django-insecure-gtey#8sy1d^2cwpa3h6r7@-ei^%zlqpw=9wg-7kfpkq@shigc2"

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "jobby",
        # Utilize the peer authentication method to connect to the database.
        # This way, we don't have to create an extra user for the dev database.
        # https://www.postgresql.org/docs/current/auth-peer.html
        "USER": getpass.getuser(),
    }
}

ALLOWED_HOSTS = [".localhost", "127.0.0.1", "[::1]"]

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Required for debug_toolbar:
INTERNAL_IPS = ["127.0.0.1"]

MEDIA_ROOT = BASE_DIR / "media"
