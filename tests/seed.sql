INSERT INTO "user" (name, password) VALUES
    ('user-station-manager', 'user-station-manager'),
    ('user-red', 'user-red'),
    ('john', 'john'),
    ('jane', 'jane');
INSERT INTO route (event_id, name) VALUES
    ({event_id}, 'route-red'),
    ({event_id}, 'route-blue');
INSERT INTO role (name) VALUES
    ('station-manager'),
    ('a-role');
INSERT INTO station (event_id, name, is_start, is_end, "order") VALUES
    ({event_id}, 'station-start', true, false, 10),
    ({event_id}, 'station-blue', false, false, 20),
    ({event_id}, 'station-red', false, false, 30),
    ({event_id}, 'station-end', false, true, 40);
INSERT INTO team (event_id, confirmation_key, name, email, route_name) VALUES
    ({event_id}, 'a', 'team-red', 'email-red@example.com', 'route-red'),
    ({event_id}, 'b', 'team-blue', 'email-blue@example.com', 'route-blue'),
    ({event_id}, 'c', 'team-without-route', 'email-wr@example.com', NULL);
INSERT INTO user_role (user_name, role_name) VALUES
    ('user-station-manager', 'station-manager'),
    ('john', 'a-role');
INSERT INTO user_station (event_id, user_name, station_name) VALUES
    ({event_id}, 'user-station-manager', 'station-red'),
    ({event_id}, 'user-red', 'station-red');
INSERT INTO team_station_state (event_id, team_name, station_name, state, score) VALUES
    ({event_id}, 'team-red', 'station-end', 'arrived', 0),
    ({event_id}, 'team-red', 'station-start', 'finished', 10),
    ({event_id}, 'team-blue', 'station-blue', 'finished', 20);
INSERT INTO route_station (event_id, route_name, station_name) VALUES
    ({event_id}, 'route-red', 'station-start'),
    ({event_id}, 'route-red', 'station-red'),
    ({event_id}, 'route-red', 'station-end'),
    ({event_id}, 'route-blue', 'station-start'),
    ({event_id}, 'route-blue', 'station-blue'),
    ({event_id}, 'route-blue', 'station-end');
INSERT INTO questionnaire (event_id, name, station_name, updated) VALUES
    ({event_id}, 'questionnaire_1', 'station-blue', now()),
    ({event_id}, 'questionnaire_2', 'station-red', now()),
    ({event_id}, 'questionnaire_3', null, now())
;
INSERT INTO questionnaire_score (event_id,questionnaire, team, score, updated) VALUES
    ({event_id}, 'questionnaire_1', 'team-red', 10, now()),
    ({event_id}, 'questionnaire_2', 'team-red', 20, now()),
    ({event_id}, 'questionnaire_1', 'team-blue', 30, now())
;
