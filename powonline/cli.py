import logging
from configparser import NoOptionError, NoSectionError

import click

from powonline.model import DB, Role, Route, User
from powonline.pusher import PusherWrapper
from powonline.web import make_app

LOG = logging.getLogger(__name__)


@click.command()
@click.argument('login')
def grant_admin(login: str) -> None:
    """
    Grants the "admin" role to the user with login "login"
    """
    app = make_app()  # type: ignore
    with app.app_context():
        query = User.query.filter_by(name=login)
        user = query.one_or_none()
        if not user:
            print('No such user')
        else:
            user.roles.add(Role.get_or_create(DB.session, 'admin'))
        DB.session.commit()


@click.command()
@click.argument('login')
def revoke_admin(login: str) -> None:
    """
    Revokes the "admin" role from the user with login "login"
    """
    app = make_app()  # type: ignore
    with app.app_context():
        query = User.query.filter_by(name=login)
        user = query.one_or_none()
        if not user:
            print('No such user')
        else:
            user.roles.remove(Role.get_or_create(DB.session, 'admin'))
        DB.session.commit()


@click.command()
def list_users() -> None:
    """
    Lists the existing users in the DB
    """
    app = make_app()  # type: ignore
    with app.app_context():
        query = User.query.order_by(User.name)
        for row in query:
            print(row.name)


@click.command()
def add_local_user() -> None:
    """
    Adds a local user to the DB for login without social provider
    """
    from getpass import getpass
    login = input('Username (login): ').strip()
    password = getpass()
    if not all([login, password]):
        print('Both username and password are required.')
        return
    app = make_app()  # type: ignore
    with app.app_context():
        user = User(name=login, password=password)
        DB.session.add(user)
        DB.session.commit()


@click.command()
@click.argument('filename')
@click.argument('event-day')
def import_csv(filename: str, event_day: str) -> None:
    """
    Imports teams from a CSV file.

    FILENAME: The filename to use for import

    EVENT_DAY: The date of the event as YYYY-MM-DD

    The CSV file should use commas as separators, have one line as header and
    the following fields:
        * id: ignored
        * timestamp: used as "inserted" timestamp in the DB. Text format: "4/15/2019 22:13:14"
        * email: Contact email for the team
        * name: The (display) name of the team
        * contact: The name of the person to contact.
        * phone: The phone number of the person to contact.
        * num_participants: Number of total participants
        * num_vegetarians: Number of vegetarians
        * planned_start_time: The time where the team is scheduled to leave
        * comments: Additional comments given by the team
    """
    import csv
    from datetime import datetime

    from powonline.model import Team

    event_day = datetime.strptime(event_day, '%Y-%m-%d')

    with open(filename) as fptr:
        reader = csv.DictReader(fptr, [
            'id',
            'timestamp',
            'email',
            'name',
            'contact',
            'phone',
            'num_participants',
            'num_vegetarians',
            'planned_start_time',
            'comments',
        ])
        next(reader)

        app = make_app()  # type: ignore
        with app.app_context():
            for data in reader:
                direction, _, timestr = data[
                    'planned_start_time'].partition(' - ')
                direction = direction.strip()
                timestr = timestr.strip()

                try:
                    timedata = datetime.strptime(timestr, r'%Hh%M').time()
                    planned_start_time = datetime(
                        event_day.year, event_day.month, event_day.day,
                        timedata.hour,
                        timedata.minute,
                        0)
                    order = int(planned_start_time.strftime('%H%M'))
                except ValueError:
                    planned_start_time = None
                    order = 0

                try:
                    inserted = datetime.strptime(
                        data['timestamp'], '%m/%d/%Y %H:%M:%S')
                except ValueError:
                    inserted = None

                route = DB.session.query(Route).filter_by(name=direction)
                route = route.one_or_none()
                if not route:
                    DB.session.add(Route(name=direction))

                team = Team(
                    name = data['name'],
                    email = data['email'] if '@' in data['email'] else 'nobody@example.com',
                    order = order,
                    contact = data['contact'],
                    phone = data['phone'],
                    comments = data['comments'],
                    is_confirmed = True,
                    accepted = True,
                    inserted = inserted or datetime.now(),
                    num_vegetarians = int(data['num_vegetarians']),
                    num_participants = int(data['num_participants']),
                    planned_start_time = planned_start_time,
                    route_name = direction,
                )
                team.reset_confirmation_key()
                DB.session.add(team)
                LOG.info('Added %s', team)
            DB.session.commit()

@click.command()
@click.option('--force/--no-force', default=False)
@click.option('--fail-fast/--no-fail-fast', default=False)
@click.option('--quiet/--no-quiet', default=False)
def fetch_mails(force, fail_fast, quiet):
    import logging

    from gouge.colourcli import Simple

    import powonline.model as mdl
    from powonline.config import default
    from powonline.core import Upload
    from powonline.mailfetcher import MailFetcher

    if quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.DEBUG
        logging.getLogger('imapclient').setLevel(logging.INFO)

    Simple.basicConfig(level=log_level)

    config = default()

    pusher = PusherWrapper.create(
        config,
        config.get('pusher', 'app_id', fallback=''),
        config.get('pusher', 'key', fallback=''),
        config.get('pusher', 'secret', fallback=''),
    )

    app = make_app()  # type: ignore
    with app.app_context():

        def callback(username, filename):
            user = mdl.User.get_or_create(DB.session, username)
            db_instance = mdl.Upload.get_or_create(
                DB.session, filename, user.name)
            DB.session.commit()
            pusher.trigger('file-events', 'file-added', {
                'from': username,
                'relname': filename
            })

        try:
            host = config.get('email', 'host')
            login = config.get('email', 'login')
            password = config.get('email', 'password')
            port = config.getint('email', 'port', fallback=143)
            ssl_raw = config.get('email', 'ssl', fallback='true')
        except (NoOptionError, NoSectionError):
            LOG.error('Unable to fetchmail. No mail server configured!')
            return 1

        ssl = ssl_raw.lower()[0] in ('1', 'y', 't')
        fetcher = MailFetcher(
            host,
            login,
            password,
            ssl,
            config.get('app', 'upload_folder', fallback=Upload.FALLBACK_FOLDER),
            force=force,
            file_saved_callback=callback,
            fail_fast=fail_fast)
        fetcher.connect()
        fetcher.fetch()
        fetcher.disconnect()
        return 0
