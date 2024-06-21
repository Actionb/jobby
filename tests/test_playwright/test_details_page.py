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
def detail_page(page, add, add_url, edit_url, jobdetails_url):
    if add:
        page.goto(add_url)
    else:
        page.goto(edit_url)
    return page


################################################################################
# EDIT PAGE
################################################################################


@pytest.mark.parametrize("add", [False])
def test_detail_page_edit(detail_page, add, stellenangebot):
    """Assert that the edit page contains the data of the model instance."""
    expect(detail_page.get_by_title("Stellenangebot Titel")).to_have_text(stellenangebot.titel)
    expect(detail_page.get_by_title("Arbeitsort")).to_contain_text(stellenangebot.arbeitsort)
    expect(detail_page.get_by_title("Arbeitgeber")).to_contain_text(stellenangebot.arbeitgeber)
    expect(detail_page.get_by_title("Eintrittsdatum")).to_contain_text(localize(stellenangebot.eintrittsdatum))


@pytest.mark.parametrize("add", [False])
def test_edit_can_update(detail_page, add, stellenangebot, watchlist_item, watchlist):
    """
    Assert that the user can update the Stellenangebot without it being removed
    from the watchlist.
    """
    detail_page.get_by_label("Notizen").fill("Foo")
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name=re.compile("suche", re.IGNORECASE)).click()
    stellenangebot.refresh_from_db()
    assert stellenangebot.notizen == "Foo"
    assert watchlist.on_watchlist(stellenangebot)


@pytest.mark.skip(reason="Not yet implemented.")
@pytest.mark.parametrize("add", [False])
def test_edit_can_remove_from_watchlist(detail_page, add, stellenangebot, watchlist_item, watchlist, watchlist_url):
    """Assert that the user can remove the Stellenangebot from the watchlist."""
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name=re.compile("entfernen", re.IGNORECASE)).click()
    assert not watchlist.on_watchlist(stellenangebot)
    assert detail_page.url == watchlist_url
    assert stellenangebot.pk
    assert not Stellenangebot.objects.filter(pk=stellenangebot.pk).exists()


@pytest.mark.skip(reason="Not yet implemented.")
def test_edit_can_remove_from_watchlist_additional_user_data(
    page,
    edit_url,
    stellenangebot,
    watchlist_item,
    watchlist,
    watchlist_url,
):
    """
    Assert that the user can remove the Stellenangebot from the watchlist when
    the user has added additional data to the Stellenangebot object.
    """
    stellenangebot.notizen = "Foo"
    stellenangebot.save()
    page.goto(edit_url)
    with page.expect_request_finished():
        page.get_by_role("button", name=re.compile("entfernen", re.IGNORECASE)).click()
    assert not watchlist.on_watchlist(stellenangebot)
    assert page.url == watchlist_url
    # The Stellenangebot object should not have been deleted:
    assert Stellenangebot.objects.filter(pk=stellenangebot.pk).exists()


@pytest.mark.parametrize("add", [False])
def test_edit_can_add_to_watchlist(detail_page, add, stellenangebot, watchlist, watchlist_url):
    """Assert that the user can add the Stellenangebot to the watchlist."""
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name=re.compile("merkliste", re.IGNORECASE)).click()
    assert watchlist.on_watchlist(stellenangebot)
    assert detail_page.url == watchlist_url


################################################################################
# ADD PAGE
################################################################################


@pytest.mark.parametrize("add", [True])
def test_detail_page_add(detail_page, add, add_data):
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
def test_add_gets_jobdetails(detail_page, add, add_data, requests_mock, jobdetails_url, job_description_text, get_url):
    """
    Assert that the Stellenangebot add page automatically fetches the job
    description from the job's original detail page.
    """
    try:
        # Give the request some time to finish, if it hasn't yet.
        def predicate(request):
            return request.url == get_url("get_angebot_beschreibung", kwargs={"refnr": add_data["refnr"]})

        with detail_page.expect_request_finished(predicate, timeout=2000):
            pass
    except playwright.sync_api.Error:
        # Assume that the request had already finished.
        pass
    assert requests_mock.request_history[0].url == jobdetails_url + add_data["refnr"]
    expect(detail_page.get_by_test_id("job-description")).to_contain_text(job_description_text)


@pytest.mark.skip(reason="Not yet implemented.")
@pytest.mark.parametrize("add", [True])
def test_add_can_add_to_watchlist(detail_page, add, add_data, watchlist, get_url):
    """
    Assert that the user can add the Stellenangebot to the watchlist from the
    add page.
    """
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name="Speichern & Merken").click()
    queryset = Stellenangebot.objects.filter(refnr=add_data["refnr"])
    assert queryset.exists()
    stellenangebot = queryset.get()
    assert watchlist.on_watchlist(stellenangebot)
    assert detail_page.url == get_url("stellenangebot_edit", kwargs={"id": stellenangebot.pk})


@pytest.mark.parametrize("add", [True])
def test_add_and_back_to_search_results(detail_page, add, add_data, watchlist, get_url):
    """
    Assert that the "Merken > Suche" save button sends the user back to the
    search page.
    """
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name=re.compile("suche", re.IGNORECASE)).click()
    queryset = Stellenangebot.objects.filter(refnr=add_data["refnr"])
    assert queryset.exists()
    stellenangebot = queryset.get()
    assert watchlist.on_watchlist(stellenangebot)
    assert detail_page.url == get_url("suche")


@pytest.mark.parametrize("add", [True])
def test_add_and_to_watchlist(detail_page, add, add_data, watchlist, watchlist_url):
    """
    Assert that the "Merken > Merkliste" save button sends the user to the
    watchlist page.
    """
    with detail_page.expect_request_finished():
        detail_page.get_by_role("button", name=re.compile("merkliste", re.IGNORECASE)).click()
    queryset = Stellenangebot.objects.filter(refnr=add_data["refnr"])
    assert queryset.exists()
    stellenangebot = queryset.get()
    assert watchlist.on_watchlist(stellenangebot)
    assert detail_page.url == watchlist_url
