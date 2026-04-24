# Microsoft Identity Configuration (2026)

1.  Go to the [Azure Portal](https://portal.azure.com/).
2.  Navigate to **Microsoft Entra ID > App registrations**.
3.  Click **New registration**.
4.  **Redirect URI**: Select "Web" and add `https://<your-api-domain>/auth/callback/microsoft`.
5.  After creation, note the **Application (client) ID**.
6.  Navigate to **Certificates & secrets** and create a new **Client secret**.
7.  (Optional) If you want to restrict to a specific tenant, note the **Directory (tenant) ID**.

### App Configuration (`app.ini`)

```ini
[social:microsoft]
client_id = <your-client-id>
client_secret = <your-client-secret>
tenant = common  # Use 'common' for multi-tenant, or your tenant ID
```
