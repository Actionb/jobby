import pytest

from tests.factories import StellenangebotFactory


@pytest.fixture
def refnr():
    return "789-456-1230"


@pytest.fixture
def stellenangebot(refnr):
    return StellenangebotFactory(
        titel="Software Developer",
        refnr=refnr,
        beruf="Informatiker",
        arbeitgeber="IHK Dortmund",
        arbeitsort="Dortmund",
        eintrittsdatum="2024-07-01",
        veroeffentlicht="2024-05-30",
        modified="2024-05-22T09:00:15.099",
    )
