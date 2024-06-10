from datetime import datetime

# noinspection PyPackageRequirements
import pytest
from django.utils.timezone import make_aware

from tests.factories import StellenangebotFactory, WatchlistFactory, WatchlistItemFactory

################################################################################
# MODELS
################################################################################


@pytest.fixture
def refnr():
    return "789-456-1230"


@pytest.fixture
def modified():
    """Return the value for the ``modified`` field of the Stellenangebot model."""
    return make_aware(datetime.fromisoformat("2024-05-22T09:00:15.099"))


@pytest.fixture
def stellenangebot(refnr, modified):
    """Create a Stellenangebot instance."""
    return StellenangebotFactory(
        titel="Software Developer",
        refnr=refnr,
        beruf="Informatiker",
        arbeitgeber="IHK Dortmund",
        arbeitsort="Dortmund",
        eintrittsdatum="2024-07-01",
        veroeffentlicht="2024-05-30",
        modified=modified,
    )


@pytest.fixture
def watchlist_name():
    """Return the name for the test watchlist."""
    return "test_watchlist"


@pytest.fixture
def watchlist(watchlist_name):
    """Return the watchlist test instance."""
    return WatchlistFactory(name=watchlist_name)


@pytest.fixture
def watchlist_item(watchlist, stellenangebot):
    """Create and return a watchlist item for the watchlist test instance."""
    return WatchlistItemFactory(watchlist=watchlist, stellenangebot=stellenangebot)


################################################################################
# REQUESTS & VIEWS
################################################################################


@pytest.fixture
def request_data():
    """The data for a http request."""
    return {}


@pytest.fixture
def http_request(rf, request_data):  # TODO: rename to get_request?
    """Return a GET request."""
    return rf.get("", data=request_data)


@pytest.fixture
def post_request(rf, request_data):
    """Return a POST request."""
    return rf.post("", data=request_data)


@pytest.fixture
def view_extra_context():
    """Extra context for view instantiation."""
    return {}


@pytest.fixture
def view(view_class, http_request, view_extra_context):
    """Instantiate the given view class with the request and context."""
    view = view_class(extra_context=view_extra_context)
    view.setup(http_request)
    return view
