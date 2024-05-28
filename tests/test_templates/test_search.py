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
        Mock(titel="Software Tester"),
        Mock(titel="Software Entwickler"),
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
    assert """<li class="result-item">Software Tester</li>""" == str(rendered_results[0])
    assert """<li class="result-item">Software Entwickler</li>""" == str(rendered_results[1])
