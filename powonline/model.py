from datetime import datetime


class Team:
    def __init__(self, name='Example Team'):
        self.name = name
        self.email = 'example@example.com'
        self.order = 0
        self.cancelled = False
        self.contact = 'John Doe'
        self.phone = '1234'
        self.comments = ''
        self.is_confirmed = True
        self.confirmation_key = 'abc'
        self.accepted = True
        self.completed = False
        self.inserted = datetime.now()
        self.updated = None
        self.num_vegetarians = 3
        self.num_participants = 10
        self.planned_start_time = None
        self.effective_start_time = None
        self.finish_time = None

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Station:
    def __init__(self):
        self.name = 'Example Station'
        self.contact = 'Example Contact'
        self.phone = '12345'
        self.is_start = False
        self.is_end = False

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Route:
    def __init__(self):
        self.name = 'Example Station'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class User:
    # TODO: Should the name be the PK? Email or ID would be better.
    def __init__(self):
        self.name = 'Example Station'


class Role:
    def __init__(self):
        self.name = 'Example Station'


class Job:
    def __init__(self):
        self.action = 'example_action'
        self.args = {}
