import re
from datetime import date, datetime

import playwright.sync_api
import pytest
from django.utils.formats import localize
from django.utils.http import urlencode
from django.utils.timezone import make_aware
from jobby.models import Stellenangebot
from playwright.sync_api import expect

pytestmark = [pytest.mark.django_db, pytest.mark.pw]


@pytest.fixture
def edit_url(get_url, stellenangebot):
    return get_url("stellenangebot_edit", kwargs={"id": stellenangebot.pk})


@pytest.fixture
def add_data():
    return {
        "titel": "Software Tester",
        "refnr": "1234",
        "beruf": "Fachinformatiker",
        "arbeitgeber": "IHK Dortmund",
        "arbeitsort": "Dortmund",
        "eintrittsdatum": "2024-07-01",
        "veroeffentlicht": "2024-05-30",
        "modified": make_aware(datetime.fromisoformat("2024-05-22T09:00:15.099")),
    }


@pytest.fixture
def add_query_string(add_data):
    return urlencode(add_data)


@pytest.fixture
def add_url(get_url, add_query_string):
    return f"{get_url('stellenangebot_add')}?{add_query_string}"


@pytest.fixture
def detail_page(page, add, add_url, edit_url, jobdetails_url, request):
    if add:
        page.goto(add_url)
    else:
        # Load the fixture that adds the object to the watchlist:
        request.getfixturevalue("watchlist_item")
        page.goto(edit_url)
    return page


@pytest.fixture
def form_pane(detail_page):
    detail_page.get_by_role("tab", name="Eigene Daten").click()


@pytest.fixture
def save_button(detail_page, add):
    """Return the basic save button of the detail page."""
    if add:
        name = "Merken"
    else:
        name = "Speichern"
    return detail_page.get_by_role("button", name=name, exact=True)


@pytest.fixture
def save_button_suche(detail_page, add):
    """
    Return the button that saves the Stellenangebot and then redirects the user
    to the search page.
    """
    if add:
        name = "Merken & zur Suche"
    else:
        name = "Speichern & zur Suche"
    return detail_page.get_by_role("button", name=name, exact=True)


@pytest.fixture
def save_button_merkliste(detail_page, add):
    """
    Return the button that saves the Stellenangebot and then redirects the user
    to the watchlist.
    """
    if add:
        name = "Merken & zur Merkliste"
    else:
        name = "Speichern & zur Merkliste"
    return detail_page.get_by_role("button", name=name, exact=True)


@pytest.fixture
def remove_button(detail_page):
    """Return the button that removes the Stellenangebot from the watchlist."""
    return detail_page.get_by_role("button", name=re.compile("entfernen", re.IGNORECASE))


@pytest.fixture
def wait_for_request(detail_page):
    """Try to wait for a request to finish, if it hasn't finished yet."""

    def inner(predicate):
        try:
            with detail_page.expect_request_finished(predicate, timeout=2000):
                pass
        except playwright.sync_api.Error:
            # Assume that the request had already finished.
            pass

    return inner


################################################################################
# EDIT PAGE
################################################################################


@pytest.mark.parametrize("add", [False])
@pytest.mark.parametrize("button_pressed", ["save_button", "save_button_suche", "save_button_merkliste"])
def test_edit_save_buttons(detail_page, form_pane, add, stellenangebot, button_pressed, request):
    """
    Assert that the user can save the Stellenangebot with any of the save
    buttons.
    """
    detail_page.get_by_label("Notizen").fill("Foo")
    with detail_page.expect_request_finished():
        request.getfixturevalue(button_pressed).click()
    stellenangebot.refresh_from_db()
    assert stellenangebot.notizen == "Foo"


@pytest.mark.parametrize("add", [False])
@pytest.mark.parametrize("button_pressed", ["save_button", "save_button_suche", "save_button_merkliste"])
def test_edit_can_add_to_watchlist(detail_page, add, stellenangebot, watchlist, button_pressed, request):
    """Assert that saving the Stellenangebot adds it to the watchlist."""
    with detail_page.expect_request_finished():
        request.getfixturevalue(button_pressed).click()
    assert watchlist.on_watchlist(stellenangebot)


@pytest.mark.parametrize("add", [False])
def test_detail_page_edit_data(detail_page, add, stellenangebot):
    """Assert that the edit page contains the data of the model instance."""
    expect(detail_page.get_by_title("Stellenangebot Titel")).to_have_text(stellenangebot.titel)
    expect(detail_page.get_by_title("Arbeitsort")).to_contain_text(stellenangebot.arbeitsort)
    expect(detail_page.get_by_title("Arbeitgeber")).to_contain_text(stellenangebot.arbeitgeber)
    expect(detail_page.get_by_title("Eintrittsdatum")).to_contain_text(localize(stellenangebot.eintrittsdatum))


@pytest.mark.parametrize("add", [False])
def test_edit_can_remove_from_watchlist(detail_page, add, stellenangebot, watchlist, watchlist_url, remove_button):
    """Assert that the user can remove the Stellenangebot from the watchlist."""
    with detail_page.expect_request_finished():
        remove_button.click()
    assert not watchlist.on_watchlist(stellenangebot)
    assert stellenangebot.pk
    assert not Stellenangebot.objects.filter(pk=stellenangebot.pk).exists()
    assert detail_page.url == watchlist_url


@pytest.mark.parametrize("add", [False])
@pytest.mark.parametrize("stellenangebot_extra_data", [{"notizen": "Foo"}])
def test_edit_can_remove_additional_user_data(
    detail_page,
    add,
    stellenangebot,
    stellenangebot_extra_data,
    watchlist,
    watchlist_url,
    remove_button,
):
    """
    Assert that the user can remove the Stellenangebot from the watchlist when
    the user has added additional data to the Stellenangebot object.
    """
    with detail_page.expect_request_finished():
        remove_button.click()
    assert not watchlist.on_watchlist(stellenangebot)
    # The Stellenangebot object should not have been deleted:
    assert Stellenangebot.objects.filter(pk=stellenangebot.pk).exists()
    assert detail_page.url == watchlist_url


################################################################################
# ADD PAGE
################################################################################


@pytest.mark.parametrize("add", [True])
@pytest.mark.parametrize("button_pressed", ["save_button", "save_button_suche", "save_button_merkliste"])
def test_add_save_buttons(detail_page, add, button_pressed, request, add_data):
    """
    Assert that the user can save the Stellenangebot with any of the save
    buttons.
    """
    with detail_page.expect_request_finished():
        request.getfixturevalue(button_pressed).click()
    assert Stellenangebot.objects.filter(refnr=add_data["refnr"]).exists()


@pytest.mark.parametrize("add", [True])
@pytest.mark.parametrize("button_pressed", ["save_button", "save_button_suche", "save_button_merkliste"])
def test_add_can_add_to_watchlist(detail_page, add, add_data, watchlist, get_url, button_pressed, request):
    """Assert that saving the Stellenangebot adds it to the watchlist."""
    with detail_page.expect_request_finished():
        request.getfixturevalue(button_pressed).click()
    queryset = Stellenangebot.objects.filter(refnr=add_data["refnr"])
    assert queryset.exists()
    stellenangebot = queryset.get()
    assert watchlist.on_watchlist(stellenangebot)


@pytest.mark.parametrize("add", [True])
def test_detail_page_add_data(detail_page, add, add_data):
    """
    Assert that the Stellenangebot add page contains the data from the GET
    request query string.
    """
    expect(detail_page.get_by_title("Stellenangebot Titel")).to_have_text(add_data["titel"])
    expect(detail_page.get_by_title("Arbeitsort")).to_contain_text(add_data["arbeitsort"])
    expect(detail_page.get_by_title("Arbeitgeber")).to_contain_text(add_data["arbeitgeber"])
    localized_date = localize(date.fromisoformat(add_data["eintrittsdatum"]))
    expect(detail_page.get_by_title("Eintrittsdatum")).to_contain_text(localized_date)


@pytest.mark.parametrize("add", [True])
def test_add_gets_jobdetails(
    detail_page,
    add,
    add_data,
    requests_mock,
    jobdetails_url,
    job_description_text,
    get_url,
    wait_for_request,
):
    """
    Assert that the Stellenangebot add page automatically fetches the job
    description from the job's original detail page.
    """

    def predicate(request):
        return request.url == get_url("get_angebot_beschreibung", kwargs={"refnr": add_data["refnr"]})

    wait_for_request(predicate)
    assert requests_mock.request_history[0].url == jobdetails_url + add_data["refnr"]
    expect(detail_page.get_by_test_id("job-description")).to_contain_text(job_description_text)


@pytest.mark.parametrize("add", [True])
def test_add_saves_job_description(
    detail_page,
    add,
    add_data,
    jobdetails_url,
    job_description_html,
    get_url,
    wait_for_request,
    save_button,
):
    """
    Assert that saving from the details page adds the fetched job description
    to the Stellenangebot instance.
    """

    def predicate(request):
        return request.url == get_url("get_angebot_beschreibung", kwargs={"refnr": add_data["refnr"]})

    wait_for_request(predicate)
    with detail_page.expect_request_finished():
        save_button.click()
    saved = Stellenangebot.objects.get(refnr=add_data["refnr"])
    assert saved.beschreibung == job_description_html


@pytest.mark.parametrize("add", [True, False])
def test_save_and_back_to_search_results(detail_page, add, add_data, watchlist, get_url, save_button_suche):
    """
    Assert that the "Speichern > Suche" save button sends the user back to the
    search page.
    """
    with detail_page.expect_request_finished():
        save_button_suche.click()
    assert detail_page.url == get_url("suche")


@pytest.mark.parametrize("add", [True, False])
def test_save_and_to_watchlist(detail_page, add, add_data, watchlist, watchlist_url, save_button_merkliste):
    """
    Assert that the "Speichern > Merkliste" save button sends the user to the
    watchlist page.
    """
    with detail_page.expect_request_finished():
        save_button_merkliste.click()
    assert detail_page.url == watchlist_url
