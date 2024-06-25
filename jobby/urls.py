from django.shortcuts import redirect
from django.urls import path, reverse_lazy

from jobby.views import (
    PapierkorbView,
    StellenangebotView,
    SucheView,
    WatchlistView,
    get_beschreibung,
    papierkorb_delete,
    stellenangebot_remove,
    watchlist_remove,
    watchlist_remove_all,
    watchlist_toggle,
)

urlpatterns = [  # pragma: no cover
    path("", lambda r: redirect(reverse_lazy("suche")), name="index"),  # TODO: add a dashboard
    path("suche/", SucheView.as_view(), name="suche"),
    path("merkliste/", WatchlistView.as_view(), name="watchlist"),
    path("merkliste/toggle/", watchlist_toggle, name="watchlist_toggle"),
    path("merkliste/remove/", watchlist_remove, name="watchlist_remove"),
    path("merkliste/remove_all/", watchlist_remove_all, name="watchlist_remove_all"),
    path("angebot/", StellenangebotView.as_view(extra_context={"add": True}), name="stellenangebot_add"),
    path("angebot/<int:id>/", StellenangebotView.as_view(extra_context={"add": False}), name="stellenangebot_edit"),
    path("fetch_description/<str:refnr>/", get_beschreibung, name="get_angebot_beschreibung"),
    path("papierkorb/", PapierkorbView.as_view(), name="papierkorb"),
    path("papierkorb/delete/", papierkorb_delete, name="papierkorb_delete"),
    path("angebote/<int:id>/remove/", stellenangebot_remove, name="stellenangebot_remove"),
]
