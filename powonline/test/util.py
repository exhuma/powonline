"""
Helper functions for unit-tests
"""

from datetime import datetime
from unittest.mock import create_autospec

import powonline.model as mdl


def make_dummy_team_dict(as_mock=False, **overlay):
    """
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    """
    tstamp = (
        datetime(2017, 1, 1, 10, 0) if as_mock else "2017-01-01T10:00:00+00:00"
    )
    output = {
        "name": "Example Team",
        "email": "example@example.com",
        "order": 0,
        "cancelled": False,
        "contact": "John Doe",
        "phone": "1234",
        "comments": "",
        "is_confirmed": True,
        "confirmation_key": "abc",
        "accepted": True,
        "completed": False,
        "inserted": tstamp,
        "updated": None,
        "num_vegetarians": 3,
        "num_participants": 10,
        "planned_start_time": None,
        "effective_start_time": None,
        "finish_time": None,
        "route_name": None,
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Team)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output


def make_dummy_station_dict(as_mock=False, **overlay):
    """
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    """
    output = {
        "name": "Example Station",
        "contact": "Example Contact",
        "phone": "12345",
        "is_start": False,
        "is_end": False,
        "order": 500,
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Station)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output


def make_dummy_route_dict(as_mock=False, **overlay):
    """
    Creates a new dict as it might be returned by the backend. This should only
    contain JSON serialisable values!

    Using the "overlay" kwargs, you can change default values.
    """
    output = {
        "name": "Example Route",
        "color": "#000000",
    }
    output.update(**overlay)
    if as_mock:
        mock = create_autospec(mdl.Route)
        for k, v in output.items():
            setattr(mock, k, v)
        return mock
    else:
        return output
