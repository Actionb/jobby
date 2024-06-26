from zoneinfo import ZoneInfo

# noinspection PyPackageRequirements
import factory
from jobby.models import Stellenangebot, Watchlist, WatchlistItem


class AngebotFactory(factory.Factory):
    titel = factory.Faker("job")
    refnr = factory.Faker("phone_number")
    beruf = factory.Faker("job")
    arbeitgeber = factory.Faker("company")
    arbeitsort = factory.Faker("city")
    eintrittsdatum = factory.Faker("date")
    aktuelleVeroeffentlichungsdatum = factory.Faker("date")
    modifikationsTimestamp = factory.Faker("date_time", locale="de_DE", tzinfo=ZoneInfo(key="Europe/Berlin"))


class StellenangebotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stellenangebot

    titel = factory.Faker("job")
    refnr = factory.Faker("phone_number")
    beruf = factory.Faker("job")
    arbeitgeber = factory.Faker("company")
    arbeitsort = factory.Faker("city")
    eintrittsdatum = factory.Faker("date")
    veroeffentlicht = factory.Faker("date")
    modified = factory.Faker("date_time", locale="de_DE", tzinfo=ZoneInfo(key="Europe/Berlin"))


class WatchlistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Watchlist


class WatchlistItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WatchlistItem
