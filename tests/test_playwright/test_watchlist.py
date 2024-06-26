import re

import pytest
from playwright.sync_api import expect

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db, pytest.mark.pw]


@pytest.fixture
def watchlist_items(watchlist, stellenangebot):
    watchlist.add_watchlist_item(stellenangebot)
    watchlist.add_watchlist_item(StellenangebotFactory())
    return watchlist.get_stellenangebote()


@pytest.fixture
def watchlist_page(page, get_url, watchlist_name):
    page.goto(get_url("watchlist"))
    return page


def get_watchlist_items(page):
    """Return the 'tr' elements that represent watchlist items."""
    return page.locator("tr.watchlist-item")


def test_remove(watchlist_items, watchlist_page, watchlist):
    """
    Assert that, on the watchlist page, the user can remove a Stellenangebot
    from the watchlist.
    """
    watchlist_item = get_watchlist_items(watchlist_page).first
    remove_button = watchlist_item.get_by_role("button", name=re.compile("entfernen", re.IGNORECASE))
    with watchlist_page.expect_request_finished():
        remove_button.click()
    expect(get_watchlist_items(watchlist_page)).to_have_count(1)
    assert watchlist.items.count() == 1


def test_remove_all(watchlist_items, watchlist_page, watchlist):
    """
    Assert that, on the watchlist page, the user can remove all watchlist items
    from the watchlist.
    """
    with watchlist_page.expect_request_finished():
        watchlist_page.get_by_role("button", name="Alle entfernen").click()
    expect(get_watchlist_items(watchlist_page)).to_have_count(0)
    assert watchlist.items.count() == 0


def test_can_search(watchlist_items, watchlist_page):
    """Assert that the user can filter the watchlist items."""
    watchlist_page.get_by_label("Textsuche").fill(watchlist_items.first().titel)
    with watchlist_page.expect_request_finished():
        watchlist_page.get_by_role("button", name="Suche").click()
    expect(get_watchlist_items(watchlist_page)).to_have_count(1)


@pytest.mark.parametrize("stellenangebot_extra_data", [{"expired": True}])
def test_expired(watchlist_items, watchlist_page, stellenangebot_extra_data):
    """Assert that expired watchlist items are marked as such."""
    watchlist_item = get_watchlist_items(watchlist_page).first
    expect(watchlist_item).to_have_class(re.compile("expired"))
    expect(watchlist_item).to_have_class(re.compile("opacity-25"))
    expect(watchlist_item).to_contain_text("Stellenangebot nicht mehr verfügbar")
