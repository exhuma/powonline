"""
Utility functions to work with pusher.com for distributed live-events.
"""
import logging
from abc import ABCMeta, abstractmethod

import pusher  # type: ignore

LOG = logging.getLogger(__name__)


class PusherWrapper(metaclass=ABCMeta):
    def __init__(self, channels):
        self.channels = channels
        LOG.debug("pusher wrapper instantiated with channels: %r", channels)

    @staticmethod
    def create(config, app_id, key, secret):
        channels = {
            "team-event-channel": config.get(
                "pusher_channels",
                "team_station_state",
                fallback="team-station-state-dev",
            ),
            "file-event-channel": config.get(
                "pusher_channels", "file", fallback="file-events-dev"
            ),
        }

        if not all([app_id, key, secret]):
            LOG.warning(
                "Instantiating NullPusher "
                "(not all values found in application config!"
            )
            return NullPusher(channels)
        else:
            return DefaultPusher(app_id, key, secret, channels)

    @abstractmethod
    def trigger(self, channel, event, payload):
        raise NotImplementedError("Not yet implemented")

    def send_team_event(self, event, payload):
        channel = self.channels["team-event-channel"]
        self.trigger(channel, event, payload)

    def send_file_event(self, event, payload):
        channel = self.channels["file-event-channel"]
        self.trigger(channel, event, payload)


class NullPusher(PusherWrapper):
    """
    A fake pusher implementation which does nothing but logging.
    """

    def trigger(self, channel, event, payload):
        LOG.debug(
            "NullPusher triggered with %r, %r, %r", channel, event, payload
        )


class DefaultPusher(PusherWrapper):
    def __init__(self, app_id, key, secret, channels):
        super().__init__(channels)
        self._pusher = pusher.Pusher(
            app_id=app_id, key=key, secret=secret, cluster="eu", ssl=True
        )
        LOG.debug("Successfully created pusher client for app-id %r", app_id)

    def trigger(self, channel, event, payload):
        LOG.debug("Sending event %r to channel %r", event, channel)
        try:
            self._pusher.trigger(channel, event, payload)
        except:
            LOG.exception("Unable to contact pusher!")
