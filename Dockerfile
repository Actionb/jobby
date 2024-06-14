FROM python:3.12-alpine as build

RUN ["apk", "update"]
RUN ["apk", "add", "build-base", "apache2-dev"]
RUN ["python3", "-m", "pip", "install", "--upgrade", "pip", "wheel"]

WORKDIR /jobby
COPY requirements requirements
RUN ["python3", "-m", "pip", "install", "-r", "requirements/base.txt"]

FROM python:3.12-alpine as final

RUN ["apk", "update", "&&", "upgrade"]
# libpq required by psycopg2
RUN ["apk", "add", "libpq", "apache2"]

COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

WORKDIR /jobby
RUN ["mkdir", "static"]
COPY manage.py .
COPY project project
COPY docker-entrypoint.sh .
COPY jobby jobby

EXPOSE 80
