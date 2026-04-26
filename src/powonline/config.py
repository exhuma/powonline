"""
Config loading for powonline.

The primary config format is an INI file located via config_resolver's XDG
search path (group "mamerwiselen", app "powonline", file "app.ini", schema
version 2.3+).

Container / 12-factor overrides
--------------------------------
Set ``POWONLINE_CONFIG_FILE`` to bypass XDG discovery and load a specific
path directly.  This is the recommended approach when the INI file is
delivered as a volume mount.

The following secrets can be supplied as environment variables.  When set
they shadow the corresponding INI values so the INI file does not need to
contain production secrets:

  POWONLINE_JWT_SECRET          → [security] jwt_secret
  POWONLINE_JWT_LIFETIME        → [security] jwt_lifetime  (seconds, integer)
  POWONLINE_GOOGLE_CLIENT_SECRET → [social:google] client_secret
  POWONLINE_OIDC_CLIENT_SECRET  → [social:oidc] client_secret
  POWONLINE_EMAIL_LOGIN         → [email] login
  POWONLINE_EMAIL_PASSWORD      → [email] password
  POWONLINE_ALLOWED_ORIGINS     → [app] allowed_origins  (comma-separated)

Legal / data-controller identity (used in auto-generated legal documents):

  POWONLINE_SITE_NAME           → [legal] site_name
  POWONLINE_SITE_URL            → [legal] site_url
  POWONLINE_CONTACT_EMAIL       → [legal] contact_email

Asset storage:

  POWONLINE_ASSET_DIR           → [app] asset_dir
    Directory where uploaded event assets (e.g. favicons) are stored.
    Defaults to /var/lib/powonline/assets when not set.
"""

import os
from configparser import ConfigParser
from functools import lru_cache

from config_resolver.core import get_config


def _apply_env_overrides(cfg: ConfigParser) -> None:
    """Overlay environment variable values onto the parsed config."""

    def _set(section: str, key: str, env_var: str) -> None:
        value = os.environ.get(env_var)
        if value is None:
            return
        if not cfg.has_section(section):
            cfg.add_section(section)
        cfg.set(section, key, value)

    _set("security", "jwt_secret", "POWONLINE_JWT_SECRET")
    _set("security", "jwt_lifetime", "POWONLINE_JWT_LIFETIME")
    _set("social:google", "client_secret", "POWONLINE_GOOGLE_CLIENT_SECRET")
    _set("social:oidc", "client_secret", "POWONLINE_OIDC_CLIENT_SECRET")
    _set("email", "login", "POWONLINE_EMAIL_LOGIN")
    _set("email", "password", "POWONLINE_EMAIL_PASSWORD")
    _set("app", "allowed_origins", "POWONLINE_ALLOWED_ORIGINS")
    _set("legal", "site_name", "POWONLINE_SITE_NAME")
    _set("legal", "site_url", "POWONLINE_SITE_URL")
    _set("legal", "contact_email", "POWONLINE_CONTACT_EMAIL")
    _set("app", "asset_dir", "POWONLINE_ASSET_DIR")


@lru_cache
def default() -> ConfigParser:
    config_file = os.environ.get("POWONLINE_CONFIG_FILE")
    if config_file:
        cfg = ConfigParser()
        cfg.read(config_file)
    else:
        lookup = get_config(
            group_name="mamerwiselen",
            app_name="powonline",
            lookup_options={
                "version": "2.3",
                "filename": "app.ini",
            },
        )
        cfg = lookup.config

    _apply_env_overrides(cfg)
    return cfg


def get_asset_dir() -> str:
    """Return the filesystem path where event assets (favicons etc.) are stored.

    Reads from [app] asset_dir in the INI config (or POWONLINE_ASSET_DIR env
    var).  Falls back to /var/lib/powonline/assets when not configured.
    """
    try:
        cfg = default()
        return cfg.get("app", "asset_dir", fallback="/var/lib/powonline/assets")
    except Exception:
        return "/var/lib/powonline/assets"
