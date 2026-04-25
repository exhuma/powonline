# GitHub OAuth Configuration (2026)

1.  Go to **Settings > Developer settings > OAuth Apps** on GitHub.
2.  Click **New OAuth App**.
3.  **Homepage URL**: `https://<your-frontend-domain>`.
4.  **Authorization callback URL**: `https://<your-api-domain>/auth/callback/github`.
5.  Click **Register application**.
6.  Generate a **Client Secret**.

### App Configuration (`app.ini`)

```ini
[social:github]
client_id = <your-client-id>
client_secret = <your-client-secret>
```
