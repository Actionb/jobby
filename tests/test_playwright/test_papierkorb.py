import re

import pytest
from playwright.sync_api import expect

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db, pytest.mark.pw]


@pytest.fixture
def orphans():
    """Create Stellenangebot instances that are not on a watchlist."""
    return [
        StellenangebotFactory(),
        StellenangebotFactory(),
    ]


@pytest.fixture
def papierkorb_page(page, get_url):
    page.goto(get_url("papierkorb"))
    return page


def get_trash_items(page):
    """Return the Papierkorb items."""
    return page.locator("tr.trash-item")


def get_delete_button(trash_item):
    """Return the button that deletes a Papierkorb item."""
    return trash_item.get_by_title(re.compile("löschen"))


def test_papierkorb_view(orphans, papierkorb_page):
    """Assert that the Papierkorb contains the expected items."""
    trash_items = get_trash_items(papierkorb_page)
    expect(trash_items).to_have_count(2)
    expect(trash_items.nth(0)).to_contain_text(orphans[0].titel)
    expect(trash_items.nth(1)).to_contain_text(orphans[1].titel)


def test_can_delete(orphans, papierkorb_page):
    """Assert that items can be deleted from the Papierkorb page."""
    trash_items = get_trash_items(papierkorb_page)
    delete_button = get_delete_button(trash_items.first)
    delete_button.click()
    trash_items = get_trash_items(papierkorb_page)
    expect(trash_items).to_have_count(1)

    # Delete the second item as well:
    delete_button = get_delete_button(trash_items.first)
    delete_button.click()
    expect(papierkorb_page.locator("body")).to_contain_text("Dein Papierkorb ist leer!")
