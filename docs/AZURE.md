# Deploy to Azure (Container Apps + Postgres) with Okta

## 1. Okta: create the app (Okta admin console)
1. Applications > Create App Integration > **OIDC - OpenID Connect** > **Web Application**.
2. Sign-in redirect URI: leave a placeholder for now; you get the real one from step 2.
3. Assignments: assign only the people/groups who should use the CRM.
4. Copy the **Client ID**, **Client secret**, and your **issuer** (Security > API > Authorization
   Servers > `default` > Issuer URI, e.g. `https://yourorg.okta.com/oauth2/default`).

## 2. Azure: create everything (Cloud Shell, bash)
```bash
git clone https://github.com/tpatel99/crm.git && cd crm
az login && az account set --subscription "<your subscription>"
OKTA_ISSUER=https://yourorg.okta.com/oauth2/default \
OKTA_CLIENT_ID=... OKTA_CLIENT_SECRET=... \
LOCATION=eastus ./infra/deploy.sh
```
It prints the app URL and the redirect URI. Back in Okta, set the sign-in redirect URI to
`https://<app-fqdn>/api/auth/callback`. Open the app URL: the first person to sign in becomes admin.

## 3. Auto-deploy from GitHub (optional)
Create a service principal with a federated credential so GitHub can deploy without stored passwords:
```bash
SUB=$(az account show --query id -o tsv)
APP_ID=$(az ad app create --display-name crm-github --query appId -o tsv)
az ad sp create --id $APP_ID
az role assignment create --assignee $APP_ID --role Contributor --scope /subscriptions/$SUB/resourceGroups/rg-crm
az ad app federated-credential create --id $APP_ID --parameters '{
  "name":"github-main","issuer":"https://token.actions.githubusercontent.com",
  "subject":"repo:tpatel99/crm:ref:refs/heads/main","audiences":["api://AzureADTokenExchange"]}'
```
In GitHub > repo Settings > Secrets and variables > Actions:
- Secrets: `AZURE_CLIENT_ID` (= $APP_ID), `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- Variables: `AZURE_RG`=rg-crm, `AZURE_APP`=crm-app, `ACR_NAME`=<the ACR name the script printed>

## Notes
- The app refuses to start unless Okta and `SECRET_KEY` are set (unless `AUTH_DISABLED=true`).
- Postgres allows Azure services only. Backups are on by default (7 days); raise retention in the portal if needed.
- Registry admin credentials are used for simplicity; move to managed identity when hardening.
- Tables are created at startup; add Alembic migrations before changing the schema with real data.
