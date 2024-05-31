from unittest.mock import Mock

import pytest
from django import forms


@pytest.fixture
def form():
    """Return the template context item for the form."""
    return forms.Form()


@pytest.fixture
def results():
    """Return the template context item for the search results."""
    return [
        Mock(titel="Software Tester", beruf="Informatiker", arbeitsort="Dortmund"),
    ]


@pytest.fixture
def context(form, results):
    """Return the context for a template."""
    return {"form": form, "results": results}


@pytest.fixture
def template_name():
    """Return the template name under test."""
    return "jobby/suche.html"


@pytest.fixture
def rendered_results(soup):
    """Return the rendered result items."""
    return soup.find_all(class_="result-item")


@pytest.mark.parametrize("results", [[Mock()]])
def test_search_with_results_has_ergebnisse(rendered_template, results):
    assert "Ergebnisse" in rendered_template


@pytest.mark.parametrize("results", [[]])
def test_search_no_results_no_ergebnisse(rendered_template, results):
    assert "Ergebnisse" not in rendered_template
    assert "Keine Angebote gefunden!" in rendered_template


def test_results_rendering(rendered_results):
    paragraphs = rendered_results[0].find_all("p")
    assert str(paragraphs[0]) == """<p><span class="fw-bold">Titel:</span> Software Tester</p>"""
    assert str(paragraphs[1]) == """<p><span class="fw-bold">Beruf:</span> Informatiker</p>"""
    assert str(paragraphs[2]) == """<p><span class="fw-bold">Arbeitsort:</span> Dortmund</p>"""
