from configparser import ConfigParser

from config_resolver import get_config


def default() -> ConfigParser:
    lookup = get_config(
        group_name='mamerwiselen', app_name='powonline',
        filename='app.ini', lookup_options={'version': '2.3'})
    return lookup.config
