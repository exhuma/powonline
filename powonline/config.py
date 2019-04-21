from config_resolver import Config


def default() -> Config:
    config = Config('mamerwiselen', 'powonline', version='2.0')
    return config
