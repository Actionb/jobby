from unittest.mock import Mock

import pytest
from django import forms
from django.core.paginator import Paginator


@pytest.fixture
def form():
    """Return the template context item for the form."""
    return forms.Form()


@pytest.fixture
def results():
    """Return the template context item for the search results."""
    return [
        Mock(titel="Software Tester", arbeitsort="Dortmund", arbeitgeber="IHK Dortmund", eintrittsdatum="2024-05-31"),
    ]


@pytest.fixture
def results_context(results):
    return {"results": results}


@pytest.fixture
def pagination_context():
    return {}


@pytest.fixture
def context(http_request, form, results_context, pagination_context):
    """Return the context for a template."""
    return {
        "request": http_request,
        "form": form,
        **results_context,
        **pagination_context,
    }


@pytest.fixture
def template_name():
    """Return the template name under test."""
    return "jobby/suche.html"


@pytest.fixture
def rendered_results(soup):
    """Return the rendered result items."""
    return soup.find_all(class_="result-item")


def test_search_with_results_has_ergebnisse(rendered_template):
    assert "Ergebnisse" in rendered_template


@pytest.mark.parametrize("results_context", [{"results": []}])
def test_search_no_results_no_ergebnisse(rendered_template, results_context):
    assert "Ergebnisse" not in rendered_template
    assert "Keine Angebote gefunden!" in rendered_template


def test_results_rendering(results, rendered_results):
    assert rendered_results[0].h3.string == results[0].titel
    assert rendered_results[0].find("span", class_="arbeitsort").string == results[0].arbeitsort
    assert rendered_results[0].find("span", class_="arbeitgeber").string == results[0].arbeitgeber
    assert rendered_results[0].find("span", class_="eintrittsdatum").string == results[0].eintrittsdatum


@pytest.mark.parametrize(
    "pagination_context",
    [{"current_page": 2, "page_range": [1, 2, Paginator.ELLIPSIS, 5], "pagination_required": True}],
)
def test_pagination(soup, pagination_context):
    pagination_container = soup.find("div", class_="pagination-container")
    assert pagination_container
    page_items = pagination_container.find_all("li")
    assert len(page_items) == 4
    assert str(page_items[0]) == """<li class="page-item"><a class="page-link" href="?page=1">1</a></li>"""
    assert str(page_items[1]) == """<li class="page-item"><a class="page-link disabled" href="#">2</a></li>"""
    assert str(page_items[2]) == """<li class="page-item"><span class="page-link disabled">…</span></li>"""
    assert str(page_items[3]) == """<li class="page-item"><a class="page-link" href="?page=5">5</a></li>"""
