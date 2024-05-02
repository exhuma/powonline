"""
This module contains tests for features implemented mainly for helping the vuejs
based frontens.
"""

import json
import logging
from unittest import TestCase

from httpx import AsyncClient

LOG = logging.getLogger(__name__)


def drop_all_except(dct, *keep):
    """
    Given a dictionary, and a list of keys from that dictionary, this function
    will drop all keys from the dictionary *except* those given in the list
    *keep*.

    This is used to make testing larger dictionary structures a bit easier (but
    less complete).
    """
    dict_keys = list(dct.keys())
    for key in dict_keys:
        if key not in keep:
            del dct[key]


async def test_fetch_assignments_api(test_client: AsyncClient):
    response = await test_client.get("/assignments")
    assert response.status_code == 200, response.text
    result_data = json.loads(response.text)

    # To be testing a bit easier, we drop all the irrelevant keys
    for k1, k2 in [
        ("stations", "route-red"),
        ("stations", "route-blue"),
        ("teams", "route-red"),
        ("teams", "route-blue"),
    ]:
        for obj in result_data[k1][k2]:
            drop_all_except(obj, "name")

    expected = {
        "stations": {
            "route-red": [
                {"name": "station-red"},
                {"name": "station-start"},
                {"name": "station-end"},
            ],
            "route-blue": [
                {"name": "station-blue"},
                {"name": "station-start"},
                {"name": "station-end"},
            ],
        },
        "teams": {
            "route-red": [{"name": "team-red"}],
            "route-blue": [{"name": "team-blue"}],
        },
    }
    TestCase().assertCountEqual(
        result_data["stations"]["route-red"],
        expected["stations"]["route-red"],
    )
    TestCase().assertCountEqual(
        result_data["stations"]["route-blue"],
        expected["stations"]["route-blue"],
    )
    TestCase().assertCountEqual(
        result_data["teams"]["route-red"], expected["teams"]["route-red"]
    )
    TestCase().assertCountEqual(
        result_data["teams"]["route-blue"], expected["teams"]["route-blue"]
    )
