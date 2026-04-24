# Generic OIDC Configuration (2026)

This can be used for Keycloak, Auth0, Okta, etc.

### App Configuration (`app.ini`)

```ini
[social:oidc]
client_id = <your-client-id>
client_secret = <your-client-secret>
discovery_url = https://<your-idp>/.well-known/openid-configuration
```

### Redirect URI

The callback URL is `https://<your-api-domain>/auth/callback/oidc`.
