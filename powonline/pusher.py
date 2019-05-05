'''
Utility functions to work with pusher.com for distributed live-events.
'''
import logging
from abc import ABCMeta, abstractmethod

import pusher

LOG = logging.getLogger(__name__)


class PusherWrapper(metaclass=ABCMeta):

    @staticmethod
    def create(app_id, key, secret):

        if not all([app_id, key, secret]):
            LOG.warning('Instantiating NullPusher '
                        '(not all values found in application config!')
            return NullPusher()
        else:
            return DefaultPusher(app_id, key, secret)

    @abstractmethod
    def trigger(self, channel, event, payload):
        raise NotImplementedError('Not yet implemented')


class NullPusher(PusherWrapper):
    '''
    A fake pusher implementation which does nothing but logging.
    '''
    def trigger(self, channel, event, payload):
        LOG.debug('NullPusher triggered with %r, %r, %r',
                  channel, event, payload)


class DefaultPusher(PusherWrapper):

    def __init__(self, app_id, key, secret):
        super().__init__()
        self._pusher = pusher.Pusher(
            app_id=app_id,
            key=key,
            secret=secret,
            cluster='eu',
            ssl=True
        )
        LOG.debug('Successfully created pusher client for app-id %r', app_id)

    def trigger(self, channel, event, payload):
        LOG.debug('Sending event %r to channel %r', event, channel)
        try:
            self._pusher.trigger(channel, event, payload)
        except:
            LOG.exception('Unable to contact pusher!')
