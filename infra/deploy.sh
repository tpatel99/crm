#!/usr/bin/env bash
# One-time Azure setup: resource group, container registry, Postgres, Container App.
# Run in Azure Cloud Shell (bash) or anywhere `az login` works.
#   OKTA_ISSUER=... OKTA_CLIENT_ID=... OKTA_CLIENT_SECRET=... ./infra/deploy.sh
set -euo pipefail

: "${OKTA_ISSUER:?set OKTA_ISSUER}" "${OKTA_CLIENT_ID:?set OKTA_CLIENT_ID}" "${OKTA_CLIENT_SECRET:?set OKTA_CLIENT_SECRET}"
RG=${RG:-rg-crm}
LOCATION=${LOCATION:-eastus}
SUFFIX=${SUFFIX:-$(openssl rand -hex 3)}          # keeps globally-unique names unique
ACR=${ACR:-crm${SUFFIX}}                           # container registry (letters/digits only)
PG=${PG:-crm-pg-${SUFFIX}}                         # postgres server
ENV_NAME=${ENV_NAME:-crm-env}
APP=${APP:-crm-app}
PG_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)

echo "==> Resource group"
az group create -n "$RG" -l "$LOCATION" -o none

echo "==> Container registry"
az acr create -g "$RG" -n "$ACR" --sku Basic --admin-enabled true -o none

echo "==> PostgreSQL flexible server (takes a few minutes)"
az postgres flexible-server create -g "$RG" -n "$PG" -l "$LOCATION" \
  --admin-user crmadmin --admin-password "$PG_PASSWORD" \
  --sku-name Standard_B1ms --tier Burstable --storage-size 32 --version 16 \
  --public-access 0.0.0.0 --yes -o none          # 0.0.0.0 = allow Azure services only
az postgres flexible-server db create -g "$RG" -s "$PG" -d crm -o none
DB_URL="postgresql+psycopg://crmadmin:${PG_PASSWORD}@${PG}.postgres.database.azure.com:5432/crm?sslmode=require"

echo "==> Build image in the registry (no local Docker needed)"
az acr build -r "$ACR" -t crm:latest . -o none

echo "==> Container Apps environment + app"
az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOCATION" -o none
ACR_USER=$(az acr credential show -n "$ACR" --query username -o tsv)
ACR_PASS=$(az acr credential show -n "$ACR" --query 'passwords[0].value' -o tsv)
az containerapp create -g "$RG" -n "$APP" --environment "$ENV_NAME" \
  --image "$ACR.azurecr.io/crm:latest" --target-port 8000 --ingress external \
  --registry-server "$ACR.azurecr.io" --registry-username "$ACR_USER" --registry-password "$ACR_PASS" \
  --min-replicas 1 --max-replicas 1 --cpu 0.5 --memory 1Gi \
  --secrets secret-key="$SECRET_KEY" db-url="$DB_URL" okta-secret="$OKTA_CLIENT_SECRET" \
  --env-vars SECRET_KEY=secretref:secret-key DATABASE_URL=secretref:db-url \
             OKTA_CLIENT_SECRET=secretref:okta-secret OKTA_ISSUER="$OKTA_ISSUER" \
             OKTA_CLIENT_ID="$OKTA_CLIENT_ID" BASE_URL=https://placeholder -o none

FQDN=$(az containerapp show -g "$RG" -n "$APP" --query properties.configuration.ingress.fqdn -o tsv)
az containerapp update -g "$RG" -n "$APP" --set-env-vars BASE_URL="https://$FQDN" -o none

cat <<MSG

Done. App URL:            https://$FQDN
Okta redirect URI to add: https://$FQDN/api/auth/callback
Resource names for the GitHub workflow: RG=$RG ACR=$ACR APP=$APP
MSG
