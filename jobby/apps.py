from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobby"

    def ready(self):
        import jobby.apis.bundesagentur_api  # noqa  # register the api
