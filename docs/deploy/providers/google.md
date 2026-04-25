# Google OAuth2 Configuration (2026)

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project or select an existing one.
3.  Navigate to **APIs & Services > OAuth consent screen**. Configure it for "External".
4.  Navigate to **APIs & Services > Credentials**.
5.  Click **Create Credentials > OAuth client ID**.
6.  Select **Web application**.
7.  **Authorized Redirect URIs**: Add `https://<your-api-domain>/auth/callback/google`.
8.  Note the **Client ID** and **Client Secret**.

### App Configuration (`app.ini`)

```ini
[social:google]
client_id = <your-client-id>
client_secret = <your-client-secret>
```

Alternatively, use `POWONLINE_GOOGLE_CLIENT_SECRET` environment variable to shadow the secret.
