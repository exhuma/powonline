from config_resolver import get_config

def test_config():
    lookup = get_config(group_name='mamerwiselen', app_name='powonline',
                        lookup_options=dict(filename='test.ini'))
    return lookup.config
