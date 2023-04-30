import json
import logging
import unittest
from textwrap import dedent
from unittest.mock import patch

import jwt
import pytest
from config_resolver import get_config
from flask_testing import TestCase
from sqlalchemy import text
from util import (
    make_dummy_route_dict,
    make_dummy_station_dict,
    make_dummy_team_dict,
)

import powonline.core as core
from powonline.model import DB
from powonline.web import make_app

LOG = logging.getLogger(__name__)


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


class AuthClientWrapper:
    """
    A class to wrap a flask test client and intercept calls injecting an auth
    header into the request.
    """

    def __init__(self, client, header):
        self.client = client
        self.header = header

    def put(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = self.header
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = self.header
        return self.client.delete(*args, **kwargs)

    def post(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = self.header
        return self.client.post(*args, **kwargs)

    def get(self, *args, **kwargs):
        headers = kwargs.setdefault("headers", {})
        headers["Authorization"] = self.header
        return self.client.get(*args, **kwargs)


class BaseAuthTestCase(TestCase):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        lookup = get_config(
            "powonline", "mamerwiselen", lookup_options={"filename": "test.ini"}
        )
        lookup.config.read_string(
            dedent(
                """\
            [security]
            jwt_secret = testing
            secret_key = secret
            """
            )
        )
        return make_app(lookup.config)

    def setUp(self):
        if self.USERNAME:
            payload = {
                "username": self.USERNAME,
                "roles": self.ROLES,
            }
            auth_header = "Bearer %s" % jwt.encode(payload, "testing")
            self.app = AuthClientWrapper(self.client, auth_header)
        else:
            self.app = self.client

        with open(here("seed_cleanup.sql")) as seed:
            try:
                DB.session.execute(text(seed.read()))
                DB.session.commit()
            except Exception as exc:
                LOG.exception("Unable to execute cleanup seed")
                DB.session.rollback()
        with open(here("seed.sql")) as seed:
            DB.session.execute(text(seed.read()))
            DB.session.commit()

        self.maxDiff = None

    def tearDown(self):
        DB.session.remove()


class TestPublicAPIAsAdmin(BaseAuthTestCase):
    USERNAME = "user-red"
    ROLES = ["admin"]

    def test_fetch_list_of_teams_all(self):
        with patch("powonline.resources.core") as _core:
            _core.Team.all.return_value = []
            self.app.get("/team")
            _core.Team.all.assert_called_with(DB.session)

    def test_fetch_list_of_teams_by_route(self):
        with patch("powonline.resources.core") as _core:
            _core.Team.assigned_to_route.return_value = []
            self.app.get("/team?assigned_route=foo")
            _core.Team.assigned_to_route.assert_called_with(DB.session, "foo")

    def test_fetch_list_of_teams_quickfilter_without_route(self):
        with patch("powonline.resources.core") as _core:
            _core.Team.quickfilter_without_route.return_value = []
            self.app.get("/team?quickfilter=without_route")
            _core.Team.quickfilter_without_route.assert_called_with(DB.session)

    def test_fetch_list_of_stations(self):
        with patch("powonline.resources.core") as _core:
            _core.Station.all.return_value = [
                make_dummy_station_dict(as_mock=True, name="station1"),
                make_dummy_station_dict(as_mock=True, name="station2"),
                make_dummy_station_dict(as_mock=True, name="station3"),
            ]
            response = self.app.get("/station")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        items = data["items"]
        expected = [
            make_dummy_station_dict(name="station1"),
            make_dummy_station_dict(name="station2"),
            make_dummy_station_dict(name="station3"),
        ]
        self.assertCountEqual(items, expected)

    def test_fetch_list_of_routes(self):
        with patch("powonline.resources.core") as _core:
            _core.Route.all.return_value = [
                make_dummy_route_dict(as_mock=True, name="route1"),
                make_dummy_route_dict(as_mock=True, name="route2"),
                make_dummy_route_dict(as_mock=True, name="route3"),
            ]
            response = self.app.get("/route")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        items = data["items"]
        expected = [
            make_dummy_route_dict(name="route1"),
            make_dummy_route_dict(name="route2"),
            make_dummy_route_dict(name="route3"),
        ]
        self.assertCountEqual(items, expected)

    def test_update_team(self):
        replacement_team = make_dummy_team_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/team/old-team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_team),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_team_dict(name="foo", contact="new-contact")
        expected.pop("inserted")
        expected.pop("updated")
        inserted = data.pop("inserted", None)
        updated = data.pop("updated", None)
        self.assertIsNotNone(inserted)
        self.assertIsNotNone(updated)
        self.assertEqual(data, expected)

    def test_update_own_station(self):
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/station-red",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_station_dict(name="foo", contact="new-contact")
        self.assertEqual(data, expected)

    def test_update_other_station(self):
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/not-my-station",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_station_dict(name="foo", contact="new-contact")
        self.assertEqual(data, expected)

    def test_update_route(self):
        replacement_route = make_dummy_route_dict(
            name="foo", contact="new-contact"
        )

        with patch("powonline.resources.core") as _core:
            mocked_route = make_dummy_route_dict(
                as_mock=True, name="foo", contact="new-contact"
            )
            _core.Route.upsert.return_value = mocked_route
            response = self.app.put(
                "/route/old-route",
                headers={"Content-Type": "application/json"},
                data=json.dumps(replacement_route),
            )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_route_dict(name="foo")
        self.assertEqual(data, expected)

    def test_create_team(self):
        new_team = make_dummy_team_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_team),
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_team_dict(name="foo", contact="new-contact")
        self.assertEqual(data, expected)

    def test_create_station(self):
        new_station = make_dummy_station_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/station",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_station),
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_station_dict(name="foo", contact="new-contact")
        self.assertEqual(data, expected)

    def test_create_route(self):
        new_route = make_dummy_route_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/route",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_route),
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        expected = make_dummy_route_dict(name="foo")
        self.assertEqual(data, expected)

    def test_delete_team(self):
        response = self.app.delete("/team/example-team")
        self.assertEqual(response.status_code, 204, response.data)

    def test_delete_station(self):
        response = self.app.delete("/station/example-station")
        self.assertEqual(response.status_code, 204, response.data)

    def test_delete_route(self):
        response = self.app.delete("/route/example-route")
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_user_to_station(self):
        simpleuser = {"name": "john"}
        response = self.app.post(
            "/station/station-red/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleuser),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_user_to_two_stations(self):
        simpleuser = {"name": "john"}
        response = self.app.post(
            "/station/station-red/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleuser),
        )
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post(
            "/station/station-blue/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleuser),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_user_from_station(self):
        response = self.app.delete("/station/station-red/users/user-red")
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_route(self):
        simpleteam = {"name": "team-without-route"}
        response = self.app.post(
            "/route/route-red/teams",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleteam),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_team_to_two_routes(self):
        simpleteam = {"name": "team-without-route"}
        response = self.app.post(
            "/route/route-red/teams",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleteam),
        )
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post(
            "/route/route-blue/teams",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleteam),
        )
        self.assertEqual(response.status_code, 400, response.data)

    def test_unassign_team_from_route(self):
        response = self.app.delete("/route/route-red/teams/team-red")
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_role_to_user(self):
        simplerole = {"name": "a-role"}
        response = self.app.post(
            "/user/jane/roles",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplerole),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_role_from_user(self):
        response = self.app.delete("/user/john/roles/a-role")
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_route(self):
        simplestation = {"name": "station-red"}
        response = self.app.post(
            "/route/route-red/stations",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplestation),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_assign_station_to_two_routes(self):
        # should *pass*. A station can be on multiple routes!
        simplestation = {"name": "station-start"}
        response = self.app.post(
            "/route/route-red/stations",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplestation),
        )
        self.assertEqual(response.status_code, 204, response.data)
        response = self.app.post(
            "/route/route-blue/stations",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplestation),
        )
        self.assertEqual(response.status_code, 204, response.data)

    def test_unassign_station_from_route(self):
        response = self.app.delete("/route/route-red/stations/station-red")
        self.assertEqual(response.status_code, 204, response.data)

    def test_show_team_station_state(self):
        response = self.app.get("/team/team-red/stations/station-start")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.content_type, "application/json")
        data = json.loads(response.text)
        self.assertEqual(data["state"], "finished")

    def test_show_team_station_state_inverse(self):
        """
        Team and Station should be interchangeable in the URL
        """
        response_a = self.app.get("/station/station-start/teams/team-red")
        response_b = self.app.get("/team/team-red/stations/station-start")
        self.assertEqual(response_a.status_code, response_b.status_code)
        self.assertEqual(response_a.data, response_b.data)

    def test_advance_team_state_auto_start(self):
        """
        Advancing on a station flagged as "start" station should set the
        "effective start time" when the new state is "finished". This means the
        team left the start station and have effectively begun the route.
        """
        job = {
            "action": "advance",
            "args": {
                "station_name": "station-start",
                "team_name": "team-red",
            },
        }
        headers = {"Content-Type": "application/json"}

        # advance 6 times (cycles at least twice over the trigger state). We
        # expect the call to happen only once though!
        with patch("powonline.core.func") as _func:
            _func.now.return_value = "2018-01-01 01:02:03"
            for _ in range(6):
                self.app.post("/job", headers=headers, data=json.dumps(job))
            _func.now.assert_called_once()

        state_response = self.app.get("/station/station-start/teams/team-red")
        state = json.loads(state_response.text)
        self.assertEqual(state["state"], "finished")
        detail_response = self.app.get("/team/team-red")
        details = json.loads(detail_response.text)
        self.assertEqual(details["effective_start_time"], "2018-01-01T01:02:03")
        self.assertEqual(details["finish_time"], None)

    def test_advance_team_state_auto_finish(self):
        """
        Advancing on a station flagged as "end" station should set the
        "finish time" when the new state is "finished". This means the
        team arrived at the end station and have handed in their questionnaire.
        """
        job = {
            "action": "advance",
            "args": {
                "station_name": "station-end",
                "team_name": "team-red",
            },
        }
        headers = {"Content-Type": "application/json"}

        # advance 6 times (cycles at least twice over the trigger state). We
        # expect the call to happen only once though!
        with patch("powonline.core.func") as _func:
            _func.now.return_value = "2018-02-03 01:02:03"
            for _ in range(6):
                self.app.post("/job", headers=headers, data=json.dumps(job))
            _func.now.assert_called_once()

        state_response = self.app.get("/station/station-end/teams/team-red")
        state = json.loads(state_response.text)
        self.assertEqual(state["state"], "arrived")
        detail_response = self.app.get("/team/team-red")
        details = json.loads(detail_response.text)
        self.assertEqual(details["effective_start_time"], None)
        self.assertEqual(details["finish_time"], "2018-02-03T01:02:03")

    def test_advance_team_state(self):
        simplejob = {
            "action": "advance",
            "args": {
                "station_name": "station-start",
                "team_name": "team-red",
            },
        }
        response = self.app.post(
            "/job",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplejob),
        )
        self.assertEqual(response.status_code, 200, response.data)
        data = json.loads(response.text)
        result = data["result"]
        self.assertEqual(result, {"state": "unknown"})

    def test_scoreboard(self):
        with patch("powonline.resources.core") as _core:
            _core.scoreboard.return_value = [
                ("team1", 40),
                ("team2", 20),
                ("team3", 0),
            ]
            response = self.app.get("/scoreboard")
            data = json.loads(response.text)
            expected = [
                ["team1", 40],
                ["team2", 20],
                ["team3", 0],
            ]
            self.assertEqual(data, expected)

    def test_questionnaire_scores(self):
        with patch("powonline.rootbp.questionnaire_scores") as _qs:
            _qs.return_value = {
                "team1": {"station1": {"name": "quest1", "score": 19}}
            }
            response = self.app.get("/questionnaire-scores")
            data = json.loads(response.text)
            expected = {"team1": {"station1": {"name": "quest1", "score": 19}}}
            self.assertEqual(data, expected)

    def test_dashboard(self):
        with patch("powonline.resources.core") as _core:
            _core.Station.team_states.return_value = [
                ("team1", core.TeamState.ARRIVED, 10),
                ("team2", core.TeamState.UNKNOWN, None),
            ]
            response = self.app.get("/station/station-1/dashboard")
            data = json.loads(response.text)
            testable = {
                (row["score"], row["team"], row["state"]) for row in data
            }
            expected = {
                (10, "team1", "arrived"),
                (None, "team2", "unknown"),
            }
            self.assertEqual(testable, expected)

    def test_global_dashboard(self):
        with patch("powonline.resources.core") as _core:
            _core.global_dashboard.return_value = [
                {
                    "team": "team-red",
                    "stations": [
                        {
                            "name": "station-start",
                            "score": 10,
                            "state": "finished",
                        },
                        {
                            "name": "station-2",
                            "score": None,
                            "state": "unknown",
                        },
                    ],
                },
                {
                    "team": "team-2",
                    "stations": [
                        {
                            "name": "station-start",
                            "score": None,
                            "state": "unknown",
                        },
                        {
                            "name": "station-2",
                            "score": None,
                            "state": "unknown",
                        },
                    ],
                },
            ]
            response = self.app.get("/dashboard")
            data = json.loads(response.text)

            expected = [
                {
                    "team": "team-red",
                    "stations": [
                        {
                            "name": "station-start",
                            "score": 10,
                            "state": "finished",
                        },
                        {
                            "name": "station-2",
                            "score": None,
                            "state": "unknown",
                        },
                    ],
                },
                {
                    "team": "team-2",
                    "stations": [
                        {
                            "name": "station-start",
                            "score": None,
                            "state": "unknown",
                        },
                        {
                            "name": "station-2",
                            "score": None,
                            "state": "unknown",
                        },
                    ],
                },
            ]
            self.assertEqual(data, expected)


class TestPublicAPIAsStationManager(BaseAuthTestCase):
    USERNAME = "user-station-manager"
    ROLES = ["station_manager"]

    def test_fetch_list_of_teams(self):
        with patch("powonline.resources.core") as _core:
            _core.Team.all.return_value = []
            response = self.app.get("/team")
            self.assertLess(response.status_code, 400)

    def test_fetch_list_of_stations(self):
        with patch("powonline.resources.core") as _core:
            _core.Station.all.return_value = []
            response = self.app.get("/station")
        self.assertLess(response.status_code, 400)

    def test_fetch_list_of_routes(self):
        with patch("powonline.resources.core") as _core:
            _core.Route.all.return_value = []
            response = self.app.get("/route")
            self.assertLess(response.status_code, 400)

    def test_update_team(self):
        replacement_team = make_dummy_team_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/team/old-team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_team),
        )
        # should fail: access denied
        self.assertEqual(response.status_code, 401, response.data)

    def test_update_own_station(self):
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/station-red",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertLess(response.status_code, 400, response.data)

    def test_update_other_station(self):
        # should fail: access denied
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/old-blue",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_update_route(self):
        # should fail: access denied
        replacement_route = make_dummy_route_dict(
            name="foo", contact="new-contact"
        )

        with patch("powonline.resources.core") as _core:
            mocked_route = make_dummy_route_dict(
                as_mock=True, name="foo", contact="new-contact"
            )
            _core.Route.upsert.return_value = mocked_route
            response = self.app.put(
                "/route/old-route",
                headers={"Content-Type": "application/json"},
                data=json.dumps(replacement_route),
            )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_team(self):
        # should fail: access denied
        new_team = make_dummy_team_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_team),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_station(self):
        # should fail: access denied
        new_station = make_dummy_station_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/station",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_station),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_route(self):
        # should fail: access denied
        new_route = make_dummy_route_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/route",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_route),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_team(self):
        # should fail: access denied
        response = self.app.delete("/team/example-team")
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_station(self):
        # should fail: access denied
        response = self.app.delete("/station/example-station")
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_route(self):
        # should fail: access denied
        response = self.app.delete("/route/example-route")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_user_to_station(self):
        # should fail: access denied
        simpleuser = {"name": "john"}
        response = self.app.post(
            "/station/station-red/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleuser),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_user_from_station(self):
        # should fail: access denied
        response = self.app.delete("/station/station-red/users/user-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_team_to_route(self):
        # should fail: access denied
        simpleteam = {"name": "team-without-route"}
        response = self.app.post(
            "/route/route-red/teams",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleteam),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_team_from_route(self):
        # should fail: access denied
        response = self.app.delete("/route/route-red/teams/team-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_role_to_user(self):
        # should fail: access denied
        simplerole = {"name": "a-role"}
        response = self.app.post(
            "/user/jane/roles",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplerole),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_role_from_user(self):
        # should fail: access denied
        response = self.app.delete("/user/john/roles/a-role")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_station_to_route(self):
        # should fail: access denied
        simplestation = {"name": "station-red"}
        response = self.app.post(
            "/route/route-red/stations",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplestation),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_station_from_route(self):
        # should fail: access denied
        response = self.app.delete("/route/route-red/stations/station-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_advance_team_state(self):
        # should pass: user has permission for this station
        simplejob = {
            "action": "advance",
            "args": {
                "station_name": "station-red",
                "team_name": "team-red",
            },
        }
        response = self.app.post(
            "/job",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplejob),
        )
        self.assertEqual(response.status_code, 200, response.data)
        data = json.loads(response.text)
        result = data["result"]
        self.assertEqual(result, {"state": "arrived"})

    def test_advance_team_state_on_other_stations(self):
        # should fail: access denied
        simplejob = {
            "action": "advance",
            "args": {
                "station_name": "station-start",
                "team_name": "team-red",
            },
        }
        response = self.app.post(
            "/job",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplejob),
        )
        self.assertEqual(response.status_code, 401, response.data)


class TestPublicAPIAsAnonymous(BaseAuthTestCase):
    USERNAME = ""
    ROLES = []

    def test_fetch_list_of_teams(self):
        with patch("powonline.resources.core") as _core:
            _core.Team.all.return_value = []
            response = self.app.get("/team")
            self.assertLess(response.status_code, 400)

    def test_fetch_list_of_stations(self):
        with patch("powonline.resources.core") as _core:
            _core.Station.all.return_value = []
            response = self.app.get("/station")
        self.assertLess(response.status_code, 400, response.data)

    def test_fetch_list_of_routes(self):
        with patch("powonline.resources.core") as _core:
            _core.Route.all.return_value = []
            response = self.app.get("/route")
        self.assertLess(response.status_code, 400, response.data)

    def test_update_team(self):
        # should fail: access denied
        replacement_team = make_dummy_team_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/team/old-team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_team),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_update_own_station(self):
        # should fail: access denied
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/station-red",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_update_other_station(self):
        # should fail: access denied
        replacement_station = make_dummy_station_dict(
            name="foo", contact="new-contact"
        )

        response = self.app.put(
            "/station/not-my-station",
            headers={"Content-Type": "application/json"},
            data=json.dumps(replacement_station),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_update_route(self):
        # should fail: access denied
        replacement_route = make_dummy_route_dict(
            name="foo", contact="new-contact"
        )

        with patch("powonline.resources.core") as _core:
            mocked_route = make_dummy_route_dict(
                as_mock=True, name="foo", contact="new-contact"
            )
            _core.Route.upsert.return_value = mocked_route
            response = self.app.put(
                "/route/old-route",
                headers={"Content-Type": "application/json"},
                data=json.dumps(replacement_route),
            )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_team(self):
        # should fail: access denied
        new_team = make_dummy_team_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/team",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_team),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_station(self):
        # should fail: access denied
        new_station = make_dummy_station_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/station",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_station),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_create_route(self):
        # should fail: access denied
        new_route = make_dummy_route_dict(name="foo", contact="new-contact")

        response = self.app.post(
            "/route",
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_route),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_team(self):
        # should fail
        response = self.app.delete("/team/example-team")
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_station(self):
        # should fail: access denied
        response = self.app.delete("/station/example-station")
        self.assertEqual(response.status_code, 401, response.data)

    def test_delete_route(self):
        # should fail: access denied
        response = self.app.delete("/route/example-route")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_user_to_station(self):
        # should fail: access denied
        simpleuser = {"name": "john"}
        response = self.app.post(
            "/station/station-red/users",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleuser),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_user_from_station(self):
        # should fail: access denied
        response = self.app.delete("/station/station-red/users/user-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_team_to_route(self):
        # should fail: access denied
        simpleteam = {"name": "team-without-route"}
        response = self.app.post(
            "/route/route-red/teams",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simpleteam),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_team_from_route(self):
        # should fail: access denied
        response = self.app.delete("/route/route-red/teams/team-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_role_to_user(self):
        # should fail: access denied
        simplerole = {"name": "a-role"}
        response = self.app.post(
            "/user/jane/roles",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplerole),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_role_from_user(self):
        # should fail: access denied
        response = self.app.delete("/user/john/roles/a-role")
        self.assertEqual(response.status_code, 401, response.data)

    def test_assign_station_to_route(self):
        # should fail: access denied
        simplestation = {"name": "station-red"}
        response = self.app.post(
            "/route/route-red/stations",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplestation),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_unassign_station_from_route(self):
        # should fail: access denied
        response = self.app.delete("/route/route-red/stations/station-red")
        self.assertEqual(response.status_code, 401, response.data)

    def test_advance_team_state(self):
        # should fail: access denied
        simplejob = {
            "action": "advance",
            "args": {
                "station_name": "station-start",
                "team_name": "team-red",
            },
        }
        response = self.app.post(
            "/job",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplejob),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_advance_team_state_on_other_stations(self):
        # should fail: access denied
        simplejob = {
            "action": "advance",
            "args": {
                "station_name": "station-start",
                "team_name": "team-red",
            },
        }
        response = self.app.post(
            "/job",
            headers={"Content-Type": "application/json"},
            data=json.dumps(simplejob),
        )
        self.assertEqual(response.status_code, 401, response.data)

    def test_related_states_next(self):
        url_node = "next"  # TODO: Can be parametrised in pytest-style tests
        with patch("powonline.resources.core") as _core:
            _core.Station.team_states.return_value = [
                ("team1", core.TeamState.ARRIVED, 10),
                ("team2", core.TeamState.UNKNOWN, None),
            ]
            response = self.app.get(f"/station/station-1/{url_node}/dashboard")
            assert response.status_code == 200
            _core.Station.related.assert_called_with(
                DB.session, "station-1", core.StationRelation.NEXT
            )
            data = json.loads(response.text)
            testable = {
                (row["score"], row["team"], row["state"]) for row in data
            }
            expected = {
                (10, "team1", "arrived"),
                (None, "team2", "unknown"),
            }
            self.assertEqual(testable, expected)

    def test_related_states_previous(self):
        url_node = "previous"  # TODO: Can be parametrised in pytest-style tests
        with patch("powonline.resources.core") as _core:
            _core.Station.team_states.return_value = [
                ("team1", core.TeamState.ARRIVED, 10),
                ("team2", core.TeamState.UNKNOWN, None),
            ]
            response = self.app.get(f"/station/station-1/{url_node}/dashboard")
            assert response.status_code == 200
            _core.Station.related.assert_called_with(
                DB.session, "station-1", core.StationRelation.PREVIOUS
            )
            data = json.loads(response.text)
            testable = {
                (row["score"], row["team"], row["state"]) for row in data
            }
            expected = {
                (10, "team1", "arrived"),
                (None, "team2", "unknown"),
            }
            self.assertEqual(testable, expected)

    def test_related_states_invalid_state(self):
        """
        If a user specifies an invalid state, we want a 4xx error, not a 5xx error
        """
        response = self.app.get(
            f"/station/station-1/this-state-is-wrong/dashboard"
        )
        assert response.status_code == 400
        assert "this-state-is-wrong" in response.text
