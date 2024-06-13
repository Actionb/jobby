"""
Install script for the jobby app.

USAGE:
    python install.py --uid="$(id -u)" --gid="$(id -g)" --password=supersecret
"""

import argparse
import os
import platform
import secrets
import subprocess
from pathlib import Path

JOBBY_ENV_FILE = """# Environment variables for the jobby app.

# Database connection parameters:
DB_NAME=jobby
DB_USER=jobby
DB_HOST=db
DB_PORT=5432

# Set the settings to use to the "production" settings:
DJANGO_SETTINGS_MODULE = "project.settings.prod"

# The URL path at which the WSGI application will be mounted in the docker container.
# e.g.: MOUNT_POINT=/foo => site available under example.com/foo
MOUNT_POINT=/jobby
"""

DOCKER_ENV_FILE_TEMPLATE = """# Environment variables for docker compose.
# (note that this file should live in the project root)

DB_DATA_DIR = {data_dir}
CONFIG_DIR = {app_config_dir}

# Set UID and GID so we can specify the user for the postgres service and its
# data volume: https://stackoverflow.com/a/56904335/9313033
# Note that this is not necessary under Windows as docker volumes are using
# SMB network shares:
# https://devilbox.readthedocs.io/en/latest/howto/uid-and-gid/find-uid-and-gid-on-win.html#docker-for-windows
{uid}
{gid}
"""


class NotSupported(Exception):

    def __init__(self, msg="This operating system is not supported.", *args, **kwargs):
        # noinspection PyArgumentList
        super().__init__(msg, *args, **kwargs)


def get_parser():
    parser = argparse.ArgumentParser(description="Install the jobby app")
    parser.add_argument("--uid", dest="user_id", help="The User ID for the postgres container", type=int)
    parser.add_argument("--gid", dest="group_id", help="The Group ID for the postgres container", type=int)
    parser.add_argument("--password", dest="passwd", help="Password for the database", type=str, default="foo")
    parser.add_argument(
        "--allowedhosts",
        dest="allowed",
        help="Comma-separated list of allowed host names for the Django settings 'ALLOWED_HOSTS'",
        type=str,
        default="localhost,127.0.0.1",
    )
    return parser


def write_jobby_env_file(app_config_dir: Path):
    """
    Create the .env file that contains the environment variables for the app
    container.
    """
    # TODO: let user override vars when calling setup.py
    with open(app_config_dir / ".env", "w") as f:
        f.write(JOBBY_ENV_FILE)


def write_docker_env_file(
    app_config_dir: Path,
    data_dir: Path,
    user_id: int | None = None,
    group_id: int | None = None,
):
    """
    Write the .env file that contains the environment variables required for
    docker compose.
    """
    # If the user did not specify a UID, leave these vars commented out:
    uid = "# UID = 1000"
    gid = "# GID = 1000"
    if user_id:
        uid = f"UID = {user_id}"
        if group_id:
            gid = f"GID = {group_id}"

    env = DOCKER_ENV_FILE_TEMPLATE.format(app_config_dir=app_config_dir, data_dir=data_dir, uid=uid, gid=gid)
    with open(Path(__file__).parent / ".env", "w") as f:
        f.write(env)


def _generate_secret_key() -> str:
    """
    Generate the SECRET_KEY for the Django settings.

    See: https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-SECRET_KEY
    """
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(allowed_chars) for _ in range(50))


def write_secrets(app_config_dir, allowed, key, passwd):
    """Write the files containing the secrets into the user config directory."""
    secrets_dir = app_config_dir / ".secrets"
    secrets_dir.mkdir(exist_ok=True)
    for file_name, value in [(".allowedhosts", allowed), (".key", key), (".passwd", passwd)]:
        with open(secrets_dir / file_name, "w") as f:
            f.write(value)


def get_config_home() -> Path:
    """Return the default directory for config files (os-dependent)."""
    system = platform.system()
    if system == "Linux":
        return os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    elif system == "Windows":
        # TODO: implement
        raise NotSupported()
    else:
        raise NotSupported()


def get_data_home() -> Path:
    """Return the default directory for the user data (os-dependent)."""
    system = platform.system()
    if system == "Linux":
        return os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    elif system == "Windows":
        # TODO: implement
        raise NotSupported()
    else:
        raise NotSupported()


def get_data_directory():
    """Return the directory where the app's database data should be stored."""
    return get_data_home() / "jobby" / "data"


def get_config_directory():
    """Return the directory where the app's user configs should be stored."""
    return get_config_home() / "jobby"


def setup_data_directory():
    """Create the directories for the database data."""
    directory = get_data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory.parent / "README.txt", "w") as f:
        f.write("This is where the database data of the jobby app is stored.")
    return directory


def setup_config_directory():
    """Create the directories for the user config files."""
    directory = get_config_directory()
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / "README.txt", "w") as f:
        f.write("This is where the user config of the jobby app is stored.")
    return directory


def install(passwd: str, allowed: str, user_id: int | None = None, group_id: int | None = None):
    """
    Setup directories for the database data and config files. Then create the
    docker containers.
    """
    print("This sets up directories for persistent storage and config files.")
    print(f"Database data directory: {get_data_directory()}")
    print(f"Config directory: {get_config_directory()}")
    print(f"Database password: {passwd}")
    if input("Continue? [y/n]: ").lower().strip() not in ("y", "yes", "j", "ja", "ok"):
        print("Aborted.")
        return

    # Create directories:
    data_dir = setup_data_directory()
    app_config_dir = setup_config_directory()

    # TODO: ask for confirmation if overriding existing stuff
    # Write secrets and env files:
    write_secrets(app_config_dir, allowed=allowed, key=_generate_secret_key(), passwd=passwd)
    write_jobby_env_file(app_config_dir)
    write_docker_env_file(app_config_dir, data_dir, user_id, group_id)

    # Start containers:
    print("Creating docker containers...")
    subprocess.run(["docker", "compose", "up", "-d"])


if __name__ == "__main__":
    _parser = get_parser()
    install(**vars(_parser.parse_args()))
