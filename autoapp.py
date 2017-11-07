'''
Script to simplify the development instance.
'''
from argparse import ArgumentParser
from config_resolver import Config
from getpass import getpass

from powonline.web import make_app
from powonline.util import colorize_werkzeug, getch
from gouge.colourcli import Simple


def get_args():
    '''
    Parse command-line arguments and return the parsed namespace.
    '''
    parser = ArgumentParser()
    tasks = parser.add_mutually_exclusive_group(required=True)
    tasks.add_argument('--set-password', action='store_true',
                       help=('Set a password for a user. If the user does not '
                             'yet exist, it will be created.'))
    tasks.add_argument('--run', action='store_true',
                       help='Run the development server')
    return parser.parse_args()


def set_password(app):
    username = input('Username: ').strip()
    password = getpass('Password: ')
    if not username:
        return

    print('Should the user have admin-rights [y/N]? ')
    char = getch()
    is_admin = char.lower() == 'y'

    app.set_password(username, password, is_admin)


def main():
    '''
    The main entry-point
    '''

    Simple.basicConfig(level=0)
    config = Config('mamerwiselen', 'powonline', version='1.0')
    args = get_args()

    colorize_werkzeug()
    APP = make_app(config)

    if args.set_password:
        set_password(APP)
    elif args.run:
        APP.run(debug=True, host='0.0.0.0')


if __name__ == '__main__':
    main()
