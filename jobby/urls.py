from django.urls import path

from jobby.views import StellenangebotView, SucheView, WatchlistView, watchlist_toggle

urlpatterns = [
    path("", SucheView.as_view(), name="suche"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("watchlist/toggle/", watchlist_toggle, name="watchlist_toggle"),
    path("angebot/", StellenangebotView.as_view(extra_context={"add": True}), name="stellenangebot_add"),
    path("angebot/<int:id>/", StellenangebotView.as_view(extra_context={"add": False}), name="stellenangebot_edit"),
]
