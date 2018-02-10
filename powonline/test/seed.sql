TRUNCATE 
    "user",
    role,
    route,
    route_station,
    station,
    team,
    team_station_state,
    user_role,
    user_station
;
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
INSERT INTO station (name) VALUES
    ('station-start'),
    ('station-end'),
    ('station-red'),
    ('station-blue');
INSERT INTO team (name, email, route_name) VALUES
    ('team-red', 'email-red', 'route-red'),
    ('team-blue', 'email-blue', 'route-blue'),
    ('team-without-route', 'email-wr', NULL);
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
