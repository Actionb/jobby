from django.urls import path

from jobby.views import SucheView

urlpatterns = [
    path("", SucheView.as_view(), name="suche"),
]
