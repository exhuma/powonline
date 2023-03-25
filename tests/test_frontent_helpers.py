"""
This module contains tests for features implemented mainly for helping the vuejs
based frontens.
"""
import json
import logging
from textwrap import dedent

from flask_testing import TestCase
from pytest import fixture

import powonline.model as model
from powonline.web import make_app

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


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


@fixture
def with_config(test_config):
    test_config.read_string(
        dedent(
            """\
        [security]
        jwt_secret = %s
        """
            % ("testing",)
        )
    )
    return make_app(test_config).test_client()


class TestFrontendHelpers(TestCase):
    def setUp(self):
        self.app = self.client  # <-- avoiding unrelated diffs for now.
        #     Can be removed in a later commit

        with open(here("seed_cleanup.sql")) as seed:
            try:
                model.DB.session.execute(seed.read())
                model.DB.session.commit()
            except Exception as exc:
                LOG.exception("Unable to execute cleanup seed")
                model.DB.session.rollback()
        with open(here("seed.sql")) as seed:
            model.DB.session.execute(seed.read())
            model.DB.session.commit()

        self.maxDiff = None

    def tearDown(self):
        model.DB.session.remove()


def test_fetch_assignments_api(with_config):
    result = with_config.get("/assignments")
    result_data = json.loads(result.data.decode(result.charset))

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
