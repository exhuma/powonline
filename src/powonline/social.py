"""
OAuth2 provider implementations.

All providers share a common async interface:
  - authorization_url(redirect_uri, state, code_challenge) -> str
  - exchange_code(code, redirect_uri, code_verifier) -> dict
  - get_user_info(access_token) -> dict  (keys: name, email, picture)

Providers are resolved by name via Social.create(config, provider_name).
"""

import logging
from configparser import ConfigParser
from urllib.parse import urlencode

import httpx

LOG = logging.getLogger(__name__)

# Label displayed in the frontend for each provider key.
PROVIDER_LABELS = {
    "google": "Google",
    "facebook": "Facebook",
    "github": "GitHub",
    "microsoft": "Microsoft",
    "oidc": "SSO",
}


class Social:
    @staticmethod
    def create(config: ConfigParser, provider_name: str):
        providers = {
            "google": Google,
            "facebook": Facebook,
            "github": GitHub,
            "microsoft": Microsoft,
            "oidc": GenericOIDC,
        }
        cls = providers.get(provider_name)
        if cls is None:
            return None
        return cls.from_config(config)

    @staticmethod
    def available_providers(config: ConfigParser) -> list[dict]:
        """Return a list of configured providers as {name, label} dicts."""
        candidates = ["google", "facebook", "github", "microsoft", "oidc"]
        result = []
        for name in candidates:
            try:
                provider = Social.create(config, name)
                if provider is not None:
                    result.append(
                        {
                            "name": name,
                            "label": PROVIDER_LABELS.get(name, name.title()),
                        }
                    )
            except ValueError:
                pass
        return result


class Google:
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    SCOPE = "openid email profile"

    @staticmethod
    def from_config(config: ConfigParser):
        if not config.has_section("social:google"):
            return None
        return Google(
            client_id=config.get("social:google", "client_id"),
            client_secret=config.get("social:google", "client_secret"),
        )

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def authorization_url(
        self, redirect_uri: str, state: str, code_challenge: str
    ) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.SCOPE,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
        }
        return self.AUTHORIZATION_URL + "?" + urlencode(params)

    async def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code_verifier": code_verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "picture": data.get("picture", ""),
            }


class Facebook:
    AUTHORIZATION_URL = "https://www.facebook.com/v19.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
    USERINFO_URL = "https://graph.facebook.com/v19.0/me"
    SCOPE = "email,public_profile"

    @staticmethod
    def from_config(config: ConfigParser):
        if not config.has_section("social:facebook"):
            return None
        return Facebook(
            client_id=config.get("social:facebook", "client_id"),
            client_secret=config.get("social:facebook", "client_secret"),
        )

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def authorization_url(
        self, redirect_uri: str, state: str, code_challenge: str
    ) -> str:
        # Facebook supports PKCE since 2023 but does not require it.
        # We include it for consistency; it is silently ignored on older apps.
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.SCOPE,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return self.AUTHORIZATION_URL + "?" + urlencode(params)

    async def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.TOKEN_URL,
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                    "code_verifier": code_verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.USERINFO_URL,
                params={
                    "fields": "id,name,email,picture.type(large)",
                    "access_token": access_token,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            picture = ""
            try:
                picture = data["picture"]["data"]["url"]
            except (KeyError, TypeError):
                pass
            return {
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "picture": picture,
            }


class GitHub:
    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USERINFO_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"
    SCOPE = "read:user user:email"

    @staticmethod
    def from_config(config: ConfigParser):
        if not config.has_section("social:github"):
            return None
        return GitHub(
            client_id=config.get("social:github", "client_id"),
            client_secret=config.get("social:github", "client_secret"),
        )

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def authorization_url(
        self, redirect_uri: str, state: str, code_challenge: str
    ) -> str:
        # GitHub does not support PKCE yet; code_challenge is omitted.
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.SCOPE,
            "state": state,
        }
        return self.AUTHORIZATION_URL + "?" + urlencode(params)

    async def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.USERINFO_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            email = data.get("email", "")
            if not email:
                # Fetch primary verified email separately
                email_resp = await client.get(self.EMAILS_URL, headers=headers)
                if email_resp.status_code == 200:
                    for entry in email_resp.json():
                        if entry.get("primary") and entry.get("verified"):
                            email = entry["email"]
                            break

            return {
                "name": data.get("name") or data.get("login", ""),
                "email": email,
                "picture": data.get("avatar_url", ""),
            }


class Microsoft:
    """
    Microsoft identity platform (works for personal accounts, Azure AD,
    and multi-tenant apps depending on `tenant`).
    """

    @staticmethod
    def from_config(config: ConfigParser):
        if not config.has_section("social:microsoft"):
            return None
        tenant = config.get("social:microsoft", "tenant", fallback="common")
        return Microsoft(
            client_id=config.get("social:microsoft", "client_id"),
            client_secret=config.get("social:microsoft", "client_secret"),
            tenant=tenant,
        )

    def __init__(self, client_id: str, client_secret: str, tenant: str = "common"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant
        self._base = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"

    def authorization_url(
        self, redirect_uri: str, state: str, code_challenge: str
    ) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile User.Read",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return self._base + "/authorize?" + urlencode(params)

    async def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._base + "/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "name": data.get("displayName", ""),
                "email": data.get("mail") or data.get("userPrincipalName", ""),
                "picture": "",
            }


class GenericOIDC:
    """
    Generic OIDC provider (Keycloak, Auth0, Okta, etc.).

    Requires a discovery_url pointing to the
    /.well-known/openid-configuration endpoint.
    """

    @staticmethod
    def from_config(config: ConfigParser):
        if not config.has_section("social:oidc"):
            return None
        return GenericOIDC(
            client_id=config.get("social:oidc", "client_id"),
            client_secret=config.get("social:oidc", "client_secret"),
            discovery_url=config.get("social:oidc", "discovery_url"),
        )

    def __init__(self, client_id: str, client_secret: str, discovery_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.discovery_url = discovery_url
        self._metadata: dict | None = None

    async def _metadata_doc(self) -> dict:
        if self._metadata is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.discovery_url)
                resp.raise_for_status()
                self._metadata = resp.json()
        return self._metadata

    async def authorization_url(
        self, redirect_uri: str, state: str, code_challenge: str
    ) -> str:
        meta = await self._metadata_doc()
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return meta["authorization_endpoint"] + "?" + urlencode(params)

    async def exchange_code(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> dict:
        meta = await self._metadata_doc()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                meta["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        meta = await self._metadata_doc()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                meta["userinfo_endpoint"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "picture": data.get("picture", ""),
            }
