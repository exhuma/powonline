from .registration import Event, Team


def register(team: Team, event: Event) -> None:
    event.register(team)


def deregister(team: Team, event: Event) -> None:
    event.deregister(team)