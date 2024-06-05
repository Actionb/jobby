from django.urls import path

from jobby.views import SucheView, WatchlistView, watchlist_toggle

urlpatterns = [
    path("", SucheView.as_view(), name="suche"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("watchlist/toggle/", watchlist_toggle, name="watchlist_toggle"),
]
