from django.urls import path

from jobby.app.views import SucheView

urlpatterns = [
    path("", SucheView.as_view(), name="suche"),
]
