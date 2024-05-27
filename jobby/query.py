import dataclasses


@dataclasses.dataclass
class Result:
    titel: str


def query(**kwargs):
    return [
        Result("Handwerker"),
        Result("Steuerberater"),
    ]
