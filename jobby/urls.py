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
    path("", SucheView.as_view(), name="suche"),
    path("watchlist/", WatchlistView.as_view(), name="watchlist"),
    path("watchlist/toggle/", watchlist_toggle, name="watchlist_toggle"),
    path("watchlist/remove/", watchlist_remove, name="watchlist_remove"),
    path("watchlist/remove_all/", watchlist_remove_all, name="watchlist_remove_all"),
    path("angebot/", StellenangebotView.as_view(extra_context={"add": True}), name="stellenangebot_add"),
    path("angebot/<int:id>/", StellenangebotView.as_view(extra_context={"add": False}), name="stellenangebot_edit"),
    path("f/<str:refnr>/", get_beschreibung, name="get_angebot_beschreibung"),
]
