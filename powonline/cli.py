import logging

import click
from powonline.model import DB, Role, User, Route
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
