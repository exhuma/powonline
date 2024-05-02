import logging

import pytest
from pytest import fixture
from sqlalchemy.ext.asyncio import AsyncSession

from powonline import core, schema

LOG = logging.getLogger(__name__)


@pytest.mark.usefixtures("seed")
async def test_get_assignments(dbsession: AsyncSession):
    result = await core.get_assignments(dbsession)
    result_stations_a = {_.name for _ in result["stations"]["route-blue"]}
    result_stations_b = {_.name for _ in result["stations"]["route-red"]}
    result_teams_a = {_.name for _ in result["teams"]["route-blue"]}
    result_teams_b = {_.name for _ in result["teams"]["route-red"]}

    expected_stations_a = {"station-start", "station-blue", "station-end"}
    expected_stations_b = {"station-start", "station-red", "station-end"}
    expected_teams_a = {"team-blue"}
    expected_teams_b = {"team-red"}

    assert result_teams_a == expected_teams_a
    assert result_teams_b == expected_teams_b
    assert result_stations_a == expected_stations_a
    assert result_stations_b == expected_stations_b


@pytest.mark.usefixtures("seed")
async def test_scoreboard(dbsession: AsyncSession):
    result = list(await core.scoreboard(dbsession))
    expected = [
        ("team-blue", 50),
        ("team-red", 40),
        ("team-without-route", 0),
    ]
    assert result == expected


@pytest.mark.usefixtures("seed")
async def test_questionnaire_scores(dbsession: AsyncSession):
    result = await core.questionnaire_scores(dbsession)
    expected = {
        "team-red": {
            "station-blue": {"name": "questionnaire_1", "score": 10},
            "station-red": {"name": "questionnaire_2", "score": 20},
        },
        "team-blue": {"station-blue": {"name": "questionnaire_1", "score": 30}},
    }
    assert result == expected


@pytest.mark.usefixtures("seed")
async def test_set_questionnaire_score(dbsession: AsyncSession):
    _, result = await core.set_questionnaire_score(
        dbsession, "team-red", "station-blue", 40
    )
    assert result == 40

    new_data = await core.questionnaire_scores(dbsession)
    expected = {
        "team-red": {
            "station-blue": {"name": "questionnaire_1", "score": 40},
            "station-red": {"name": "questionnaire_2", "score": 20},
        },
        "team-blue": {"station-blue": {"name": "questionnaire_1", "score": 30}},
    }
    assert new_data == expected


async def test_global_dashboard(dbsession: AsyncSession, seed):
    result = await core.global_dashboard(dbsession)
    expected = [
        schema.GlobalDashboardRow.model_validate(
            {
                "team": "team-blue",
                "stations": [
                    {
                        "name": "station-blue",
                        "score": 20,
                        "state": core.TeamState.FINISHED,
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
            }
        ),
        schema.GlobalDashboardRow.model_validate(
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
            }
        ),
        schema.GlobalDashboardRow.model_validate(
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
            }
        ),
    ]
    assert result == expected
