# Azure deployment plan — PS04

## Architecture
- **Compute:** Azure App Service for Containers runs the FastAPI application.
- **Image registry:** Azure Container Registry (ACR) stores versioned Docker images.
- **Identity:** GitHub Actions uses OpenID Connect (OIDC) with `azure/login`; do not store a client secret.
- **Data:** The prototype uses SQLite for easy local reproduction. For a multi-instance production deployment, replace SQLite with Azure Database for PostgreSQL or Azure SQL. Do not rely on an ephemeral container filesystem for persistent production data.
- **Monitoring:** Enable App Service application logging and Application Insights; record request failures, latency, classifier confidence and approval events. Do not log full ticket messages or sensitive personal information by default.

## Required GitHub configuration
Create these **repository secrets**:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

Create these **repository variables**:
- `AZURE_RESOURCE_GROUP`
- `AZURE_WEBAPP_NAME`
- `AZURE_ACR_NAME`
- `AZURE_ACR_LOGIN_SERVER` (for example, `myregistry.azurecr.io`)

Configure a federated credential in Microsoft Entra ID for this GitHub repository and branch/environment. Grant the identity only the required roles, such as AcrPush on the registry and appropriate deployment permissions on the web app. Use the official Azure OIDC documentation when setting this up. Never commit credentials.

## Deployment outline
1. Create a resource group, ACR, and Linux App Service configured for a custom container.
2. Configure the web app to pull the image from ACR using managed identity where possible.
3. Set `WEBSITES_PORT=8000` in App Service configuration.
4. Run the GitHub Actions workflow manually from **Actions → Deploy to Azure App Service → Run workflow**.
5. Verify `/health` and `/docs`, then inspect application logs.
6. Before production use, move persistent state to a managed database and configure authentication, rate limits, backups, retention, and access controls.

## Cost control
Use the lowest suitable development tier, stop/delete resources when not in use, set budget alerts, and avoid paid AI endpoints. Live deployment is optional for this assessment.
