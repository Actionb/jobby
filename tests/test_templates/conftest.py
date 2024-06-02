# noinspection PyPackageRequirements
import pytest

# noinspection PyPackageRequirements
from bs4 import BeautifulSoup
from django.template.loader import render_to_string


@pytest.fixture
def rendered_template(template_name, context):
    """Render the template with the given context."""
    return render_to_string(template_name, context)


@pytest.fixture
def soup(rendered_template):
    """Parse the rendered template with BeautifulSoup."""
    return BeautifulSoup(rendered_template, "html.parser")
