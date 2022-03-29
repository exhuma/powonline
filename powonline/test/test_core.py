import logging
from textwrap import dedent

from flask_testing import TestCase

from powonline import core, model
from powonline.test.conftest import test_config
from powonline.web import make_app

LOG = logging.getLogger(__name__)


def here(localname):
    from os.path import dirname, join

    return join(dirname(__file__), localname)


class CommonTest(TestCase):

    SQLALCHEMY_DATABASE_URI = test_config().get("db", "dsn")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

    def create_app(self):
        config = test_config()
        config.read_string(
            dedent(
                """\
            [db]
            dsn = %s

            [security]
            jwt_secret = %s
            """
                % (CommonTest.SQLALCHEMY_DATABASE_URI, "testing")
            )
        )
        return make_app(config)

    def setUp(self):
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
        self.session = (
            model.DB.session
        )  # avoids unrelated diffs for this commit

    def tearDown(self):
        model.DB.session.remove()


class TestCore(CommonTest):
    def test_get_assignments(self):
        result = core.get_assignments(self.session)
        result_stations_a = {_.name for _ in result["stations"]["route-blue"]}
        result_stations_b = {_.name for _ in result["stations"]["route-red"]}
        result_teams_a = {_.name for _ in result["teams"]["route-blue"]}
        result_teams_b = {_.name for _ in result["teams"]["route-red"]}

        expected_stations_a = {"station-start", "station-blue", "station-end"}
        expected_stations_b = {"station-start", "station-red", "station-end"}
        expected_teams_a = {"team-blue"}
        expected_teams_b = {"team-red"}

        self.assertEqual(result_teams_a, expected_teams_a)
        self.assertEqual(result_teams_b, expected_teams_b)
        self.assertEqual(result_stations_a, expected_stations_a)
        self.assertEqual(result_stations_b, expected_stations_b)

    def test_scoreboard(self):
        result = list(core.scoreboard(self.session))
        expected = [
            ("team-red", 40),
            ("team-blue", 30),
            ("team-without-route", 0),
        ]
        self.assertEqual(result, expected)

    def test_questionnaire_scores(self):
        config = test_config()
        config.read_string(
            dedent(
                """\
            [questionnaire-map]
            questionnaire_1 = station-blue
            questionnaire_2 = station-red
            """
            )
        )
        result = core.questionnaire_scores(config, self.session)
        expected = {
            "team-red": {
                "station-blue": {"name": "questionnaire_1", "score": 10},
                "station-red": {"name": "questionnaire_2", "score": 20},
            },
            "team-blue": {
                "station-blue": {"name": "questionnaire_1", "score": 30}
            },
        }
        self.assertEqual(result, expected)

    def test_set_questionnaire_score(self):
        config = test_config()
        config.read_string(
            dedent(
                """\
            [questionnaire-map]
            questionnaire_1 = station-blue
            questionnaire_2 = station-red
            """
            )
        )
        _, result = core.set_questionnaire_score(
            config, self.session, "team-red", "station-blue", 40
        )
        self.assertEqual(result, 40)

        new_data = core.questionnaire_scores(config, self.session)
        expected = {
            "team-red": {
                "station-blue": {"name": "questionnaire_1", "score": 40},
                "station-red": {"name": "questionnaire_2", "score": 20},
            },
            "team-blue": {
                "station-blue": {"name": "questionnaire_1", "score": 30}
            },
        }
        self.assertEqual(new_data, expected)

    def test_global_dashboard(self):
        result = core.global_dashboard(self.session)
        expected = [
            {
                "team": "team-blue",
                "stations": [
                    {
                        "name": "station-blue",
                        "score": 0,
                        "state": core.TeamState.UNKNOWN,
                    },
                    {
                        "name": "station-end",
                        "score": 0,
                        "state": core.TeamState.UNKNOWN,
                    },
                    {
                        "name": "station-red",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                    {
                        "name": "station-start",
                        "score": 0,
                        "state": core.TeamState.UNKNOWN,
                    },
                ],
            },
            {
                "team": "team-red",
                "stations": [
                    {
                        "name": "station-blue",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                    {
                        "name": "station-end",
                        "score": 0,
                        "state": core.TeamState.ARRIVED,
                    },
                    {
                        "name": "station-red",
                        "score": 0,
                        "state": core.TeamState.UNKNOWN,
                    },
                    {
                        "name": "station-start",
                        "score": 10,
                        "state": core.TeamState.FINISHED,
                    },
                ],
            },
            {
                "team": "team-without-route",
                "stations": [
                    {
                        "name": "station-blue",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                    {
                        "name": "station-end",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                    {
                        "name": "station-red",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                    {
                        "name": "station-start",
                        "score": 0,
                        "state": core.TeamState.UNREACHABLE,
                    },
                ],
            },
        ]
        self.assertEqual(result, expected)


class TestTeam(CommonTest):
    def test_all(self):
        result = {_.name for _ in core.Team.all(self.session)}
        expected = {
            "team-blue",
            "team-red",
            "team-without-route",
        }
        self.assertEqual(result, expected)

    def test_quickfilter_without_route(self):
        result = list(core.Team.quickfilter_without_route(self.session))
        self.assertEqual(len(result), 1)
        result = result[0].name
        expected = "team-without-route"
        self.assertEqual(result, expected)

    def test_assigned_to_route(self):
        result = list(core.Team.assigned_to_route(self.session, "route-blue"))
        self.assertEqual(len(result), 1)
        expected = "team-blue"
        self.assertEqual(result[0].name, expected)

    def test_create_new(self):
        result = core.Team.create_new(
            self.session, {"name": "foo", "email": "foo@example.com"}
        )
        self.assertEqual(result.name, "foo")
        self.assertEqual(len(set(core.Team.all(self.session))), 4)
        self.assertIn(result, set(core.Team.all(self.session)))

    def test_upsert(self):
        core.Team.upsert(
            self.session, "team-red", {"name": "foo", "contact": "bar"}
        )
        new_names = {_.name for _ in core.Team.all(self.session)}
        self.assertEqual(new_names, {"team-blue", "team-without-route", "foo"})

    def test_delete(self):
        result = core.Team.delete(self.session, "team-red")
        self.assertEqual(len(set(core.Team.all(self.session))), 2)
        self.assertIsNone(result)

    def test_get_station_data(self):
        result1 = core.Team.get_station_data(
            self.session, "team-red", "station-start"
        )
        result2 = core.Team.get_station_data(
            self.session, "team-blue", "station-finish"
        )
        expected1 = core.TeamState.FINISHED
        expected2 = core.TeamState.UNKNOWN
        self.assertEqual(result1.state, expected1)
        self.assertEqual(result2.state, expected2)

    def test_advance_on_station(self):
        new_state = core.Team.advance_on_station(
            self.session, "team-red", "station-start"
        )
        self.assertEqual(new_state, core.TeamState.UNKNOWN)
        new_state = core.Team.advance_on_station(
            self.session, "team-red", "station-start"
        )
        self.assertEqual(new_state, core.TeamState.ARRIVED)
        new_state = core.Team.advance_on_station(
            self.session, "team-red", "station-start"
        )
        self.assertEqual(new_state, core.TeamState.FINISHED)
        new_state = core.Team.advance_on_station(
            self.session, "team-red", "station-start"
        )
        self.assertEqual(new_state, core.TeamState.UNKNOWN)


class TestStation(CommonTest):
    def test_all(self):
        result = {_.name for _ in core.Station.all(self.session)}
        expected = {
            "station-start",
            "station-red",
            "station-blue",
            "station-end",
        }
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Station.create_new(self.session, {"name": "foo"})
        self.assertEqual(result.name, "foo")
        self.assertEqual(len(set(core.Station.all(self.session))), 5)
        self.assertIn(result, set(core.Station.all(self.session)))

    def test_upsert(self):
        core.Station.upsert(
            self.session, "station-red", {"name": "foo", "contact": "bar"}
        )
        result = core.Station.all(self.session)
        names = {_.name for _ in result}
        self.assertEqual(
            names, {"station-end", "foo", "station-start", "station-blue"}
        )

    def test_delete(self):
        result = core.Station.delete(self.session, "station-red")
        self.assertEqual(len(set(core.Station.all(self.session))), 3)
        self.assertIsNone(result)

    def test_assign_user(self):
        result = core.Station.accessible_by(self.session, "john")
        self.assertEqual(result, set())
        result = core.Station.assign_user(self.session, "station-red", "john")
        self.assertTrue(result)
        result = core.Station.accessible_by(self.session, "john")
        self.assertEqual(result, {"station-red"})

    def test_team_states(self):
        result = set(core.Station.team_states(self.session, "station-start"))
        expected = {
            ("team-blue", core.TeamState.UNKNOWN, None),
            ("team-red", core.TeamState.FINISHED, 10),
        }
        self.assertEqual(result, expected)


class TestRoute(CommonTest):
    def test_all(self):
        result = {_.name for _ in core.Route.all(self.session)}
        expected = {"route-blue", "route-red"}
        self.assertEqual(result, expected)

    def test_create_new(self):
        result = core.Route.create_new(self.session, {"name": "foo"})
        stored_data = set(core.Route.all(self.session))
        self.assertEqual(result.name, "foo")
        self.assertEqual(len(stored_data), 3)
        self.assertIn(result, set(stored_data))

    def test_upsert(self):
        core.Route.upsert(self.session, "route-red", {"name": "foo"})
        result = core.Route.upsert(self.session, "foo", {"name": "bar"})
        stored_data = set(core.Route.all(self.session))
        self.assertEqual(result.name, "bar")
        self.assertEqual(len(stored_data), 2)
        self.assertIn(result, set(stored_data))

    def test_delete(self):
        result = core.Route.delete(self.session, "route-red")
        self.assertEqual(len(set(core.Route.all(self.session))), 1)
        self.assertIsNone(result)

    def test_assign_team(self):
        result = core.Route.assign_team(
            self.session, "route-red", "team-without-route"
        )
        self.assertTrue(result)
        result = {
            _.name
            for _ in core.Team.assigned_to_route(self.session, "route-red")
        }
        self.assertEqual({"team-red", "team-without-route"}, result)

    def test_unassign_team(self):
        result = core.Route.unassign_team(self.session, "route-red", "team-red")
        self.assertTrue(result)
        result = set(core.Team.assigned_to_route(self.session, "route-red"))
        self.assertEqual(set(), result)

    def test_assign_station(self):
        result = core.Route.assign_station(
            self.session, "route-red", "station-blue"
        )
        self.assertTrue(result)
        result = {
            _.name
            for _ in core.Station.assigned_to_route(self.session, "route-red")
        }
        self.assertEqual(
            {"station-start", "station-end", "station-red", "station-blue"},
            result,
        )

    def test_unassign_station(self):
        result = core.Route.unassign_station(
            self.session, "route-red", "station-red"
        )
        self.assertTrue(result)
        result = set(core.Station.assigned_to_route(self.session, "route-red"))
        self.assertNotIn(set(), result)


class TestUser(CommonTest):
    def test_assign_role(self):
        core.User.assign_role(self.session, "jane", "a-role")
        result = {_.name for _ in core.User.roles(self.session, "jane")}
        self.assertIn("a-role", result)

    def test_unassign_role(self):
        core.User.unassign_role(self.session, "john", "a-role")
        result = {_.name for _ in core.User.roles(self.session, "john")}
        self.assertNotIn("a-role", result)
