from datetime import datetime

# noinspection PyPackageRequirements
import pytest
from django.utils.timezone import make_aware
from jobby.models import _update_stellenangebot

from tests.factories import StellenangebotFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def other(refnr):
    return StellenangebotFactory.build(
        titel="Software Entwickler",
        refnr=refnr,
        beruf="",
        arbeitgeber="IHK Dortmund",
        arbeitsort="Dortmund",
        eintrittsdatum="2024-07-01",
        veroeffentlicht="2024-05-30",
        modified=make_aware(datetime.fromisoformat("2024-05-22T09:00:15.099")),
    )


def test_update_stellenangebot(stellenangebot, other):
    assert _update_stellenangebot(stellenangebot, other)
    stellenangebot.refresh_from_db()
    assert stellenangebot.titel == other.titel
    assert stellenangebot.beruf == other.beruf


def test_update_stellenangebot_identical(stellenangebot, django_assert_num_queries):
    with django_assert_num_queries(0):
        assert not _update_stellenangebot(stellenangebot, stellenangebot)


def test_update_stellenangebot_different_refnr(stellenangebot, other, django_assert_num_queries):
    other.refnr = "1"
    with django_assert_num_queries(0):
        assert not _update_stellenangebot(stellenangebot, other)
