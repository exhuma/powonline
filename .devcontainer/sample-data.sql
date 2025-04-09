--
-- PostgreSQL database dump
--

-- Dumped from database version 10.21 (Debian 10.21-1.pgdg90+1)
-- Dumped by pg_dump version 14.2

-- Started on 2023-04-10 19:02:40

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 3012 (class 0 OID 16441)
-- Dependencies: 201
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--


TRUNCATE
    public."user",
    public.auditlog,
    public.questionnaire,
    public.questionnaire_score,
    public.role,
    public.station,
    public.route_station,
    public.team_station_state,
    public.user_role,
    public.route,
    public.team
CASCADE;

INSERT INTO public."user"
    (name, password, password_is_plaintext)
VALUES
    ('admin', 'admin', true);


--
-- TOC entry 3026 (class 0 OID 16763)
-- Dependencies: 215
-- Data for Name: auditlog; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.auditlog VALUES ('2019-05-10 18:24:11.420543+00', NULL, 'station_score', 'Change score of team ''Team 1'' from None to 70 on station Station 1');
INSERT INTO public.auditlog VALUES ('2019-05-10 18:41:47.612466+00', NULL, 'station_score', 'Change score of team ''Team 2'' from None to 70 on station Station 2');
INSERT INTO public.auditlog VALUES ('2019-05-10 19:10:14.365384+00', NULL, 'station_score', 'Change score of team ''Team 3'' from None to 70 on station Station 2');
INSERT INTO public.auditlog VALUES ('2019-05-10 19:15:54.148549+00', NULL, 'station_score', 'Change score of team "Team 4" from None to 70 on station Station 1');
INSERT INTO public.auditlog VALUES ('2022-05-13 21:12:29.637072+00', NULL, 'questionnaire_score', 'Change questionnaire score of team ''Team 1'' from 0 to 35 on station Station 1');
INSERT INTO public.auditlog VALUES ('2022-05-13 21:29:54.650137+00', NULL, 'questionnaire_score', 'Change questionnaire score of team ''Team 2'' from 0 to 40 on station Station 2');
INSERT INTO public.auditlog VALUES ('2022-05-13 21:30:15.616435+00', NULL, 'questionnaire_score', 'Change questionnaire score of team ''Team 3'' from 30 to 13 on station Station 3');
INSERT INTO public.auditlog VALUES ('2022-05-13 21:43:24.094346+00', NULL, 'questionnaire_score', 'Change questionnaire score of team ''Team 4'' from 38 to 30 on station Station 3');


--
-- TOC entry 3009 (class 0 OID 16402)
-- Dependencies: 198
-- Data for Name: route; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.route VALUES ('Red', '#ff0000', '2019-05-03 21:39:24.442312+00', '2023-04-10 16:30:12.267743+00');
INSERT INTO public.route VALUES ('Blue', '#1c4587', '2019-05-03 21:39:24.442312+00', '2023-04-10 16:30:12.276059+00');


--
-- TOC entry 3010 (class 0 OID 16410)
-- Dependencies: 199
-- Data for Name: team; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.team VALUES ('Team 5', 'team5@example.com', 705, true, 'Blane Burke', '+33 913 173 9068', NULL, true, 'f8c77d83-ee57-4d4c-bf40-5cc6336b8ff7', false, false, '2022-05-13 06:42:46.973333', '2023-04-10 18:30:12.276059', 3, 4, '2022-05-13 19:30:00', '2022-05-13 21:16:56.104781', NULL, 'Blue', NULL);
INSERT INTO public.team VALUES ('Team 3', 'team3@example.com', 705, false, 'Kim Hancill', '681-06-0853', NULL, true, 'b768bcf7-bc8f-47be-a3fa-684f20538181', false, false, '2022-05-13 06:42:46.973333', '2023-04-10 18:53:12.741624', 0, 5, '2022-05-13 19:20:00', '2022-05-13 21:17:42.384855', NULL, 'Red', NULL);
INSERT INTO public.team VALUES ('Team 2', 'team2@example.com', 705, false, 'Gracie Masser', '719-54-9836', NULL, true, '4ab4ad9f-7674-417a-a863-966dbad6dd5f', false, true, '2022-05-13 06:42:46.973333', '2023-04-10 18:53:12.752866', 3, 4, '2022-05-13 19:30:00', '2022-05-13 21:16:56.104781', '2022-05-13 23:41:40.655461', 'Blue', NULL);
INSERT INTO public.team VALUES ('Team 4', 'team4@example.com', 805, false, 'Basil Redmond', '124-33-1610', NULL, true, 'fa779f47-606b-4d6d-a4e8-7a756df16877', false, false, '2022-05-13 06:42:46.973333', '2023-04-10 18:55:35.093282', 1, 5, '2022-05-13 20:30:00', '2022-05-13 21:16:59.59913', NULL, 'Blue', NULL);
INSERT INTO public.team VALUES ('Team 1', 'team1@example.com', 705, false, 'Nina Sawbridge', '231-44-8022', NULL, true, '7b3ca609-36bc-4ae8-97c4-550a1fc7d58b', false, false, '2022-05-13 06:42:46.973333', '2023-04-10 18:55:35.099985', 0, 7, '2022-05-13 19:10:00', '2022-05-13 21:18:03.747891', NULL, 'Red', NULL);


--
-- TOC entry 3020 (class 0 OID 16662)
-- Dependencies: 209
-- Data for Name: questionnaire; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questionnaire VALUES ('Questionnaire 1', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.701227+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 2', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.719363+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 3', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.723201+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 4', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.726483+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 5', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.729749+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 6', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.732597+00');
INSERT INTO public.questionnaire VALUES ('Questionnaire 0', 300, 0, '2019-05-01 13:13:18.161871+00', '2023-04-10 16:24:25.735885+00');


--
-- TOC entry 3021 (class 0 OID 16680)
-- Dependencies: 210
-- Data for Name: questionnaire_score; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 3', 30, '2022-05-13 19:34:52.793688+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 4', 18, '2022-05-13 19:01:06.417084+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 5', 28, '2022-05-13 19:18:59.733552+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 6', 44, '2022-05-13 22:21:06.309017+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 3', 30, '2022-05-13 20:44:19.002449+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 4', 22, '2022-05-13 19:59:17.365988+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 5', 39, '2022-05-13 19:21:14.803719+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 2', 30, '2022-05-13 21:48:24.570829+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 3', 30, '2022-05-13 20:37:15.111365+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 4', 24, '2022-05-13 19:52:28.752481+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 5', 34, '2022-05-13 19:22:19.625111+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 3', 30, '2022-05-13 21:02:28.57755+00', '2023-04-10 16:29:56.41461+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 4', 22, '2022-05-13 19:59:29.613682+00', '2023-04-10 16:29:56.41461+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 5', 34, '2022-05-13 19:15:00.790471+00', '2023-04-10 16:29:56.41461+00');
INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 1', 13, '2022-05-13 22:13:56.33329+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 1', 'Questionnaire 2', 20, '2022-05-13 20:58:11.205992+00', '2023-04-10 16:29:56.400028+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 1', 22, '2022-05-13 23:08:11.395605+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 2', 30, '2022-05-13 22:12:04.213632+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 2', 'Questionnaire 6', 46, '2022-05-13 23:41:32.379485+00', '2023-04-10 16:29:56.408134+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 1', 9, '2022-05-13 22:46:50.844917+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 3', 'Questionnaire 6', 44, '2022-05-13 23:44:32.449784+00', '2023-04-10 16:29:56.411422+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 1', 17, '2022-05-13 23:17:46.601404+00', '2023-04-10 16:29:56.41461+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 2', 30, '2022-05-13 22:33:40.019255+00', '2023-04-10 16:29:56.41461+00');
INSERT INTO public.questionnaire_score VALUES ('Team 4', 'Questionnaire 6', 48, '2022-05-13 23:53:40.028409+00', '2023-04-10 16:29:56.41461+00');


--
-- TOC entry 3013 (class 0 OID 16449)
-- Dependencies: 202
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.role VALUES ('admin', '2022-04-23 13:08:13.687942+00', NULL);
INSERT INTO public.role VALUES ('station_manager', '2022-04-23 13:08:13.687942+00', NULL);
INSERT INTO public.role VALUES ('staff', '2022-04-23 13:08:13.687942+00', NULL);


--
-- TOC entry 3011 (class 0 OID 16431)
-- Dependencies: 200
-- Data for Name: station; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.station VALUES ('Grillen', '', '', false, false, 500, '2019-05-03 17:54:44.641905+00', '2022-05-13 10:56:50.499784+00');
INSERT INTO public.station VALUES ('End', '', '', false, true, 999, '2019-05-01 13:09:36.064262+00', '2023-04-10 16:32:34.690931+00');
INSERT INTO public.station VALUES ('Start', 'Dave', '+358 207 658 8269', true, false, 0, '2019-04-28 10:20:02.894547+00', '2023-04-10 16:32:34.698756+00');
INSERT INTO public.station VALUES ('Station 1', NULL, NULL, false, false, 100, '2022-05-13 10:57:03.960526+00', '2023-04-10 16:32:34.702306+00');
INSERT INTO public.station VALUES ('Station 2', NULL, NULL, false, false, 200, '2022-05-13 10:57:12.638391+00', '2023-04-10 16:32:34.705679+00');
INSERT INTO public.station VALUES ('Station 3', NULL, NULL, false, false, 600, '2022-05-13 10:57:23.585683+00', '2023-04-10 16:32:34.708748+00');
INSERT INTO public.station VALUES ('Station 4', NULL, NULL, false, false, 700, '2022-05-13 10:57:32.038493+00', '2023-04-10 16:32:34.71636+00');
INSERT INTO public.station VALUES ('Station 5', NULL, NULL, false, false, 800, '2022-05-13 10:57:39.495534+00', '2023-04-10 16:32:34.719673+00');


--
-- TOC entry 3015 (class 0 OID 16476)
-- Dependencies: 204
-- Data for Name: route_station; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.route_station VALUES ('Red', 'Start', NULL, '2023-04-10 16:30:12.267743+00', '2019-05-03 21:46:54.904781+00');
INSERT INTO public.route_station VALUES ('Red', 'Grillen', NULL, '2023-04-10 16:30:12.267743+00', '2019-05-03 21:46:58.331799+00');
INSERT INTO public.route_station VALUES ('Blue', 'Start', NULL, '2023-04-10 16:30:12.276059+00', '2019-05-03 21:46:23.001368+00');
INSERT INTO public.route_station VALUES ('Blue', 'Grillen', NULL, '2023-04-10 16:30:12.276059+00', '2022-05-13 15:51:18.782062+00');
INSERT INTO public.route_station VALUES ('Red', 'End', NULL, '2023-04-10 16:32:34.690931+00', '2019-05-03 21:47:01.496128+00');
INSERT INTO public.route_station VALUES ('Blue', 'End', NULL, '2023-04-10 16:32:34.690931+00', '2022-05-13 15:51:12.9658+00');
INSERT INTO public.route_station VALUES ('Red', 'Station 1', NULL, '2023-04-10 16:32:34.702306+00', '2022-05-13 10:58:10.673939+00');
INSERT INTO public.route_station VALUES ('Blue', 'Station 1', NULL, '2023-04-10 16:32:34.702306+00', '2022-05-13 15:51:10.649738+00');
INSERT INTO public.route_station VALUES ('Red', 'Station 2', NULL, '2023-04-10 16:32:34.705679+00', '2022-05-13 10:58:11.371728+00');
INSERT INTO public.route_station VALUES ('Blue', 'Station 2', NULL, '2023-04-10 16:32:34.705679+00', '2022-05-13 15:51:14.298187+00');
INSERT INTO public.route_station VALUES ('Red', 'Station 3', NULL, '2023-04-10 16:32:34.708748+00', '2022-05-13 10:58:12.008669+00');
INSERT INTO public.route_station VALUES ('Blue', 'Station 3', NULL, '2023-04-10 16:32:34.708748+00', '2022-05-13 15:51:19.935146+00');
INSERT INTO public.route_station VALUES ('Red', 'Station 4', NULL, '2023-04-10 16:32:34.71636+00', '2022-05-13 10:58:12.58714+00');
INSERT INTO public.route_station VALUES ('Blue', 'Station 4', NULL, '2023-04-10 16:32:34.71636+00', '2022-05-13 15:50:59.464576+00');
INSERT INTO public.route_station VALUES ('Red', 'Station 5', NULL, '2023-04-10 16:32:34.719673+00', '2022-05-13 10:58:03.497283+00');
INSERT INTO public.route_station VALUES ('Blue', 'Station 5', NULL, '2023-04-10 16:32:34.719673+00', '2022-05-13 15:50:52.877608+00');


--
-- TOC entry 3024 (class 0 OID 16737)
-- Dependencies: 213
-- Data for Name: setting; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3014 (class 0 OID 16457)
-- Dependencies: 203
-- Data for Name: team_station_state; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.team_station_state VALUES ('Team 2', 'Grillen', 'arrived', NULL, '2023-04-10 16:29:56.408134+00', '2022-05-13 21:16:39.003059+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Grillen', 'arrived', NULL, '2023-04-10 16:29:56.41461+00', '2022-05-13 21:23:33.978304+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Station 1', 'finished', 50, '2023-04-10 16:32:34.702306+00', '2022-05-13 21:27:20.406562+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Station 3', 'finished', 50, '2023-04-10 16:32:34.708748+00', '2022-05-13 19:29:30.513486+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Station 3', 'finished', 70, '2023-04-10 16:32:34.708748+00', '2022-05-13 20:44:04.261003+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Station 3', 'finished', 65, '2023-04-10 16:32:34.708748+00', '2022-05-13 20:28:33.048569+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Station 4', 'finished', 55, '2023-04-10 16:32:34.71636+00', '2022-05-13 18:47:57.380436+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Station 4', 'finished', 85, '2023-04-10 16:32:34.71636+00', '2022-05-13 19:50:22.426678+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Station 4', 'finished', 55, '2023-04-10 16:32:34.71636+00', '2022-05-13 19:53:26.60101+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Station 5', 'finished', 60, '2023-04-10 16:32:34.719673+00', '2022-05-13 18:10:58.547754+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Station 5', 'finished', 40, '2023-04-10 16:32:34.719673+00', '2022-05-13 19:14:36.79192+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Station 5', 'finished', 40, '2023-04-10 16:32:34.719673+00', '2022-05-13 19:14:55.7682+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Start', 'finished', NULL, '2023-04-10 16:29:56.400028+00', '2022-05-13 21:18:03.449494+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Start', 'finished', NULL, '2023-04-10 16:29:56.408134+00', '2022-05-13 21:16:55.919181+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Grillen', 'arrived', NULL, '2023-04-10 16:29:56.411422+00', '2022-05-13 20:56:23.693076+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Start', 'finished', NULL, '2023-04-10 16:29:56.411422+00', '2022-05-13 21:17:41.345984+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Start', 'finished', NULL, '2023-04-10 16:29:56.41461+00', '2022-05-13 21:16:59.397567+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'End', 'unknown', NULL, '2023-04-10 16:32:34.690931+00', '2022-05-13 23:53:43.445908+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Station 2', 'arrived', 100, '2023-04-10 16:32:34.705679+00', '2022-05-13 22:23:04.113524+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Station 3', 'finished', 75, '2023-04-10 16:32:34.708748+00', '2022-05-13 20:52:47.611502+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'End', 'unknown', NULL, '2023-04-10 16:32:34.690931+00', '2022-05-13 23:41:40.655461+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'End', 'unknown', NULL, '2023-04-10 16:32:34.690931+00', '2022-05-13 23:44:32.67799+00');
INSERT INTO public.team_station_state VALUES ('Team 2', 'Station 1', 'finished', 30, '2023-04-10 16:32:34.702306+00', '2022-05-13 22:49:36.694175+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Station 1', 'finished', 40, '2023-04-10 16:32:34.702306+00', '2022-05-13 23:12:11.140842+00');
INSERT INTO public.team_station_state VALUES ('Team 4', 'Station 2', 'arrived', 50, '2023-04-10 16:32:34.705679+00', '2022-05-13 22:33:40.226059+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Grillen', 'finished', NULL, '2023-04-10 16:55:00.221282+00', '2022-05-13 20:05:03.212238+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'End', 'finished', NULL, '2023-04-10 16:55:00.227845+00', '2022-05-13 22:21:23.729134+00');
INSERT INTO public.team_station_state VALUES ('Team 1', 'Station 2', 'finished', 80, '2023-04-10 16:55:10.477105+00', '2022-05-13 20:58:08.41878+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Station 4', 'unknown', NULL, '2023-04-10 16:56:05.054539+00', '2022-05-13 19:32:19.195686+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Station 5', 'unknown', NULL, '2023-04-10 16:56:05.058265+00', '2022-05-13 18:18:13.570138+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Station 1', 'unknown', NULL, '2023-04-10 16:56:39.354948+00', '2022-05-13 22:12:32.664433+00');
INSERT INTO public.team_station_state VALUES ('Team 3', 'Station 2', 'unknown', NULL, '2023-04-10 16:56:39.358353+00', '2022-05-13 21:48:21.642335+00');


--
-- TOC entry 3017 (class 0 OID 16513)
-- Dependencies: 206
-- Data for Name: user_role; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.user_role VALUES ('admin', 'admin', '2023-03-26 13:59:49.370402+00', NULL);


--
-- TOC entry 3016 (class 0 OID 16495)
-- Dependencies: 205
-- Data for Name: user_station; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- TOC entry 3032 (class 0 OID 0)
-- Dependencies: 211
-- Name: message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.message_id_seq', 1, false);


--
-- TOC entry 3033 (class 0 OID 0)
-- Dependencies: 207
-- Name: oauth_connection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.oauth_connection_id_seq', 38, true);


-- Completed on 2023-04-10 19:02:42

--
-- PostgreSQL database dump complete
--
