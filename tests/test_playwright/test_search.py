import json
import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="session")
def load_page_1():
    with open(Path(__file__).parent / "search_results_page1.json") as f:
        return f.read()


@pytest.fixture(scope="session")
def load_page_2():
    with open(Path(__file__).parent / "search_results_page2.json") as f:
        return f.read()


@pytest.fixture(scope="session")
def load_search_results(load_page_1, load_page_2):
    """Read the two pages of search results."""
    return load_page_1, load_page_2


@pytest.fixture(scope="session")
def search_results_parsed(load_search_results):
    """JSON Parse the two search result pages."""
    return json.loads(load_search_results[0]), json.loads(load_search_results[1])


@pytest.fixture
def get_search_results(search_results_parsed):
    """
    Return the Stellenangebot results as returned by the API response for the
    given page_number.
    """

    def inner(page_number):
        return search_results_parsed[page_number - 1]["stellenangebote"]

    return inner


@pytest.fixture(scope="session")
def search_result_count(search_results_parsed):
    """Return the total result count."""
    return search_results_parsed[0]["maxErgebnisse"]


@pytest.fixture(autouse=True)
def get_jwt_mock():
    """Mock out retrieving a jwt token."""
    with patch("jobby.search.get_jwt", new=Mock(return_value="")) as m:
        yield m


@pytest.fixture
def search_response_status_code():
    """Return the status code for the response to the search request."""
    return 200


@pytest.fixture(autouse=True)
def search_request_mock(requests_mock, load_search_results, search_response_status_code):
    """Provide mock responses for search requests against the API."""

    def text_callback(request, _context):
        # Return the results of the requested page:
        page_number = int(request.qs["page"][0]) - 1  # qs["page"] is a list with a single value
        return load_search_results[page_number]

    requests_mock.get(
        "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs",
        text=text_callback,
        status_code=search_response_status_code,
    )


@pytest.fixture
def do_search(page, get_url):
    """Go to the search poge, fill out the search form and request results."""
    page.goto(get_url("suche"))
    page.get_by_label("was").fill("Software")
    page.get_by_label("wo").fill("Dortmund")
    with page.expect_request_finished():
        page.get_by_text("Suchen").click()
    return page


def get_result_items(page):
    """Return the 'li' elements that contain the search result data."""
    return page.locator("li.result-item")


def get_result_link(result_item):
    """Return the link to the details page of the given result."""
    return result_item.get_by_role("link")


def get_page_links(page):
    """Return the paginator links to the different pages."""
    return page.locator("a.page-link")


def get_watchlist_buttons(page):
    """Return the buttons that a search result to the watchlist."""
    return page.get_by_title("Angebot merken")


def get_hide_buttons(page):
    """Return the buttons that 'hides' a search result."""
    return page.get_by_title("Angebot ausblenden")


def get_watchlist_items(page):
    """Return the 'tr' elements that represent watchlist items."""
    return page.locator("tr.watchlist-item")


def test(page, do_search, get_search_results, search_result_count):
    # There should be a count of the total results:
    expect(page.locator("body")).to_contain_text(f"{search_result_count} Ergebnisse")
    # There should be ten pages of results:
    page_links = get_page_links(page)
    expect(page_links).to_have_count(10)
    # There should be 100 results on the current page:
    result_items = get_result_items(page)
    expect(result_items).to_have_count(100)

    watchlist_buttons = get_watchlist_buttons(page)
    search_results = get_search_results(page_number=1)
    watchlist_titles = []
    # User adds the first result item of the page to their watchlist:
    link = get_result_link(result_items.first)
    search_result_title = search_results[0]["titel"]
    expect(link).to_have_text(search_result_title)
    watchlist_titles.append(search_result_title)
    watchlist_button = watchlist_buttons.first
    with page.expect_request_finished():
        watchlist_button.click()
    expect(watchlist_button).to_have_class(re.compile("on-watchlist"))

    # User hides the second result:
    link = get_result_link(result_items.nth(1))
    expect(link).to_have_text(search_results[1]["titel"])
    get_hide_buttons(page).nth(1).click()
    expect(link).to_have_class(re.compile("link-opacity-25"))

    # User navigates to the second page of results:
    with page.expect_request_finished():
        page_links.nth(1).click()
    search_results = get_search_results(page_number=2)

    # User adds the third result item of the page to their watchlist:
    result_items = get_result_items(page)
    link = get_result_link(result_items.nth(2))
    search_result_title = search_results[2]["titel"]
    expect(link).to_have_text(search_result_title)
    watchlist_titles.append(search_result_title)
    watchlist_button = watchlist_buttons.nth(2)
    with page.expect_request_finished():
        watchlist_button.click()
    expect(watchlist_button).to_have_class(re.compile("on-watchlist"))

    # User clicks on the link of the fourth result item:
    link = get_result_link(result_items.nth(3))
    search_result_title = search_results[3]["titel"]
    # User is sent to the details view of the fourth result item:
    link.click()
    page.wait_for_url("**/angebot/**")
    expect(page.get_by_title("Stellenangebot Titel")).to_have_text(search_result_title)
    # User adds this result to their watchlist:
    with page.expect_request_finished():
        page.get_by_text(re.compile("merken", re.IGNORECASE)).click()

    watchlist_titles.append(search_result_title)
    # User navigates to the watchlist:
    page.get_by_text(re.compile("Merkliste")).click()
    page.wait_for_url("**/merkliste/")
    # The watchlist should contain 3 items:
    watchlist_items = get_watchlist_items(page)
    expect(watchlist_items).to_have_count(3)
    expect(watchlist_items.nth(0)).to_contain_text(watchlist_titles[0])
    expect(watchlist_items.nth(1)).to_contain_text(watchlist_titles[1])
    expect(watchlist_items.nth(2)).to_contain_text(watchlist_titles[2])


def test_search(page, do_search, search_result_count, get_search_results):
    """Assert that search results are displayed."""
    # There should be a count of the total results:
    expect(page.locator("body")).to_contain_text(f"{search_result_count} Ergebnisse")
    # There should be 100 results on the current page:
    result_items = get_result_items(page)
    expect(result_items).to_have_count(100)

    search_results = get_search_results(page_number=1)
    expect(get_result_link(result_items.first)).to_have_text(search_results[0]["titel"])


def test_search_pagination(page, do_search, get_search_results):
    """Assert that the search results page provides pagination links."""
    page_links = get_page_links(page)
    expect(page_links).to_have_count(10)


def test_search_page_2(page, do_search, get_search_results):
    """Assert that the user can navigate to the second page of results."""
    page_links = get_page_links(page)
    with page.expect_request_finished():
        page_links.nth(1).click()
    search_results = get_search_results(page_number=2)
    result_items = get_result_items(page)
    expect(get_result_link(result_items.first)).to_have_text(search_results[0]["titel"])


def test_search_angebot_details(page, do_search, get_search_results):
    """
    Assert that the user can navigate to a Job's detail page from the search
    results.
    """
    result_items = get_result_items(page)
    link = get_result_link(result_items.first)
    search_result_title = get_search_results(page_number=1)[0]["titel"]
    link.click()
    page.wait_for_url("**/angebot/**")
    expect(page.get_by_title("Stellenangebot Titel")).to_have_text(search_result_title)
