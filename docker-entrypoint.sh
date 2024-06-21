#!/bin/sh

# https://pypi.org/project/mod-wsgi/
# In running this command, it will not actually startup Apache. All it will do
# is create the set of configuration files and the startup script to be run.
#
# So that these are not created in the default location of a directory under
# ``/tmp``, you should use the ``--server-root`` option to specify where they
# should be placed.
#
# Having created the configuration and startup script, to start the Apache
# instance you can now run::
#
#     /etc/mod_wsgi-express-80/apachectl start
#
# To subsequently stop the Apache instance you can run::
#
#     /etc/mod_wsgi-express-80/apachectl stop
#
# You can also restart the Apache instance as necessary using::
#
#     /etc/mod_wsgi-express-80/apachectl restart
#
# Using this approach, the original options you supplied to ``setup-server``
# will be cached with the same configuration used each time. If you need to
# update the set of options, run ``setup-server`` again with the new set of
# options.

python manage.py runmodwsgi \
  --setup-only \
  --server-root=/jobby/jobby-server \
  --mount-point "$MOUNT_POINT"

# Collect static files
python manage.py collectstatic --clear --noinput --skip-checks --verbosity 0

# The entrypoint is run as pid 1, and the container will remain up and running
# as long as pid 1 is alive. Exec the command line arguments/the container
# command with pid 1 to keep the process alive.
# https://stackoverflow.com/a/55174043/9313033
exec "$@"
