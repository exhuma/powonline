INSERT INTO "user" (name) VALUES
    ('user-red'),
    ('john'),
    ('jane');
INSERT INTO route (name) VALUES
    ('route-red'),
    ('route-blue');
INSERT INTO role (name) VALUES
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
    ('john', 'a-role');
INSERT INTO user_station (user_name, station_name) VALUES
    ('user-red', 'station-red');
INSERT INTO team_station_state (team_name, station_name, state) VALUES
    ('team-red', 'station-start', 'finished');
INSERT INTO route_station (route_name, station_name) VALUES
    ('route-red', 'station-start'),
    ('route-red', 'station-red'),
    ('route-red', 'station-end'),
    ('route-blue', 'station-start'),
    ('route-blue', 'station-blue'),
    ('route-blue', 'station-end');
