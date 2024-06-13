import os
from pathlib import Path

from .base import *  # noqa

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False

# Read secrets from files
try:
    with open(BASE_DIR / ".secrets" / ".passwd") as f:
        password = f.readline().strip()
except FileNotFoundError as e:
    raise FileNotFoundError(
        "No database password file found. Create a file called '.passwd' "
        "in the '.secrets' subdirectory that contains the database password.\n"
        "HINT: run setup.sh"
    ) from e

try:
    with open(BASE_DIR / ".secrets" / ".key") as f:
        SECRET_KEY = f.readline().strip()
except FileNotFoundError as e:
    raise FileNotFoundError(
        "No secret key file found. Create a file called '.key' "
        "in the '.secrets' subdirectory that contains the secret key.\n"
        "HINT: run setup.sh"
    ) from e

try:
    with open(BASE_DIR / ".secrets" / ".allowedhosts") as f:
        ALLOWED_HOSTS = f.readline().strip().split(",")
except FileNotFoundError as e:
    raise FileNotFoundError(
        "No allowed hosts file found. Create a file called '.allowedhosts' "
        "in the '.secrets' subdirectory that contains a list of allowed "
        "host names.\n"
        "HINT: run setup.sh"
    ) from e

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "jobby"),
        "USER": os.environ.get("DB_USER", "jobby"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", 5432),
        "PASSWORD": password,
    }
}
