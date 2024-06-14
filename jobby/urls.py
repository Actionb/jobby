from django.urls import path

from jobby.views import (
    StellenangebotView,
    SucheView,
    WatchlistView,
    get_beschreibung,
    watchlist_remove,
    watchlist_remove_all,
    watchlist_toggle,
)

urlpatterns = [
    path("suche/", SucheView.as_view(), name="suche"),
    path("merkliste/", WatchlistView.as_view(), name="watchlist"),
    path("merkliste/toggle/", watchlist_toggle, name="watchlist_toggle"),
    path("merkliste/remove/", watchlist_remove, name="watchlist_remove"),
    path("merkliste/remove_all/", watchlist_remove_all, name="watchlist_remove_all"),
    path("angebot/", StellenangebotView.as_view(extra_context={"add": True}), name="stellenangebot_add"),
    path("angebot/<int:id>/", StellenangebotView.as_view(extra_context={"add": False}), name="stellenangebot_edit"),
    path("fetch_description/<str:refnr>/", get_beschreibung, name="get_angebot_beschreibung"),
]
