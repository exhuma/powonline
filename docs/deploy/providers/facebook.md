# Facebook Login Configuration (2026)

1.  Go to the [Meta for Developers](https://developers.facebook.com/) portal.
2.  Create a new app or select an existing one.
3.  Add **Facebook Login** to your app.
4.  Navigate to **Facebook Login > Settings**.
5.  **Valid OAuth Redirect URIs**: Add `https://<your-api-domain>/auth/callback/facebook`.
6.  Go to **App Settings > Basic** to find your **App ID** and **App Secret**.

### App Configuration (`app.ini`)

```ini
[social:facebook]
client_id = <your-app-id>
client_secret = <your-app-secret>
```
