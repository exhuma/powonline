INSERT INTO "user" (name, password) VALUES
    ('user-station-manager', 'user-station-manager'),
    ('user-red', 'user-red'),
    ('john', 'john'),
    ('jane', 'jane');
INSERT INTO route (name) VALUES
    ('route-red'),
    ('route-blue');
INSERT INTO role (name) VALUES
    ('station-manager'),
    ('a-role');
INSERT INTO station (name, is_start, is_end) VALUES
    ('station-start', true, false),
    ('station-end', false, true),
    ('station-red', false, false),
    ('station-blue', false, false);
INSERT INTO team (confirmation_key, name, email, route_name) VALUES
    ('a', 'team-red', 'email-red@example.com', 'route-red'),
    ('b', 'team-blue', 'email-blue@example.com', 'route-blue'),
    ('c', 'team-without-route', 'email-wr@example.com', NULL);
INSERT INTO user_role (user_name, role_name) VALUES
    ('user-station-manager', 'station-manager'),
    ('john', 'a-role');
INSERT INTO user_station (user_name, station_name) VALUES
    ('user-station-manager', 'station-red'),
    ('user-red', 'station-red');
INSERT INTO team_station_state (team_name, station_name, state, score) VALUES
    ('team-red', 'station-end', 'arrived', 0),
    ('team-red', 'station-start', 'finished', 10);
INSERT INTO route_station (route_name, station_name) VALUES
    ('route-red', 'station-start'),
    ('route-red', 'station-red'),
    ('route-red', 'station-end'),
    ('route-blue', 'station-start'),
    ('route-blue', 'station-blue'),
    ('route-blue', 'station-end');
INSERT INTO questionnaire (name) VALUES
    ('questionnaire_1'),
    ('questionnaire_2')
;
INSERT INTO questionnaire_score (questionnaire, team, score) VALUES
    ('questionnaire_1', 'team-red', 10),
    ('questionnaire_2', 'team-red', 20),
    ('questionnaire_1', 'team-blue', 30)
;
