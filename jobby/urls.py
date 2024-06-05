from django.urls import path

from jobby.views import SucheView, WatchlistView

urlpatterns = [
    path("", SucheView.as_view(), name="suche"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
]
