from configparser import ConfigParser

from config_resolver.core import get_config


def default() -> ConfigParser:
    lookup = get_config(
        group_name="mamerwiselen",
        app_name="powonline",
        lookup_options={
            "version": "2.3",
            "filename": "app.ini",
        },
    )
    return lookup.config
