import logging

from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

LOG = logging.getLogger(__name__)


class Social:
    @staticmethod
    def create(config, provider_name):
        providers = {"google": Google, "facebook": Facebook}
        provider = providers.get(provider_name)
        if not provider:
            raise ValueError(
                "Social Login via %r not yet supported" % provider_name
            )
        return provider.from_config(config)


class Google:
    @staticmethod
    def from_config(config):
        if not config.has_section("social:google"):
            return None
        client_id = config.get("social:google", "client_id")
        client_secret = config.get("social:google", "client_secret")
        redirect_uri = config.get("social:google", "redirect_uri")
        return Google(client_id, client_secret, redirect_uri)

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.authorization_base_url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
        )
        self.token_url = "https://www.googleapis.com/oauth2/v4/token"
        self.scope = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

    def process_login(self):
        client = OAuth2Session(
            self.client_id, scope=self.scope, redirect_uri=self.redirect_uri
        )
        authorization_url, state = client.authorization_url(
            self.authorization_base_url
        )
        return authorization_url, state

    def get_user_info_simple(self, token):
        client = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            token={"access_token": token},
        )
        response = client.get("https://www.googleapis.com/oauth2/v1/userinfo")
        if response.status_code != 200:
            return "Unable to fetch user-info from Google!", 500
        user_info = response.json()
        return user_info

    def get_user_info(self, state, access_url):
        client = OAuth2Session(
            self.client_id, state=state, redirect_uri=self.redirect_uri
        )
        client.fetch_token(
            self.token_url,
            client_secret=self.client_secret,
            authorization_response=access_url,
        )

        response = client.get("https://www.googleapis.com/oauth2/v1/userinfo")
        if response.status_code != 200:
            return "Unable to fetch user-info from Google!", 500
        user_info = response.json()
        return user_info


class Facebook:
    @staticmethod
    def from_config(config):
        if not config.has_section("social:facebook"):
            return None
        client_id = config.get("social:facebook", "client_id")
        client_secret = config.get("social:facebook", "client_secret")
        redirect_uri = config.get("social:facebook", "redirect_uri")
        return Facebook(client_id, client_secret, redirect_uri)

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self.authorization_base_url = "https://www.facebook.com/dialog/oauth"
        self.token_url = "https://graph.facebook.com/oauth/access_token"

    def process_login(self):
        client = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri)
        client = facebook_compliance_fix(client)
        authorization_url, state = client.authorization_url(
            self.authorization_base_url
        )
        return authorization_url, state

    def get_user_info_simple(self, token):
        client = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            token={"access_token": token},
        )
        client = facebook_compliance_fix(client)
        args = {
            "fields": ",".join(
                [
                    "email",
                    "name",
                ]
            )
        }
        response = client.get("https://graph.facebook.com/me", params=args)
        if response.status_code != 200:
            LOG.error(
                "Unable to get user-info pic from Facebook: %r", response.json()
            )
            return "Unable to fetch user-info from Facebook!", 500
        user_info = response.json()
        user_info["picture"] = None
        # Fetch profile pic separately (needs different access rights and may
        # fail)
        args = {"fields": "profile_pic"}
        response = client.get("https://graph.facebook.com/me", params=args)
        if response.status_code == 200:
            user_info["picture"] = response.json()["profile_pic"]
        else:
            LOG.error(
                "Unable to get profile pic from Facebook: %r", response.json()
            )
        return user_info

    def get_user_info(self, state, access_url):
        client = OAuth2Session(
            self.client_id, state=state, redirect_uri=self.redirect_uri
        )
        client = facebook_compliance_fix(client)
        client.fetch_token(
            self.token_url,
            client_secret=self.client_secret,
            authorization_response=access_url,
        )

        args = {
            "fields": ",".join(
                [
                    "email",
                    "name",
                ]
            )
        }
        response = client.get("https://graph.facebook.com/me", params=args)
        if response.status_code != 200:
            return "Unable to fetch user-info from Facebook!", 500
        user_info = response.json()

        # Fetch profile pic separately (needs different access rights and may
        # fail)
        args = {"fields": "profile_pic"}
        response = client.get("https://graph.facebook.com/me", params=args)
        if response.status_code == 200:
            user_info["profile_pic"] = response.json()["profile_pic"]
        return user_info
