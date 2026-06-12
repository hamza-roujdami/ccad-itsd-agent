#!/usr/bin/env bash
# ============================================================================
# Deploy the Clinical ITSM Agent backend to Azure Container Apps.
#
# Runs the agent INSIDE the lab tenant so its managed identity can reach
# Foundry + AI Search — bypassing the device-compliance / Conditional Access
# block that prevents local (Mac) auth.
#
# RUN THIS FROM AZURE CLOUD SHELL (bash) in the lab tenant:
#   1. Open https://portal.azure.com -> Cloud Shell (Bash)
#   2. Clone this repo (or upload it):  git clone <repo-url> && cd ccad-itsd-agent
#   3. Provide the ACS connection string (kept out of source):
#        export ACS_CONNECTION_STRING='endpoint=https://...;accesskey=...'
#   4. bash scripts/deploy-app.sh
#
# Idempotent: safe to re-run. Re-running rebuilds the image and updates the app.
# ============================================================================
set -euo pipefail

# ----------------------------------------------------------------------------
# Configuration (edit if your environment differs)
# ----------------------------------------------------------------------------
SUBSCRIPTION_ID="69770eff-2b73-40a9-abc7-0db9dff6c99d"
RESOURCE_GROUP="rg-ccad-itsd-dev"
LOCATION="swedencentral"
BASE_NAME="ccad-itsd"

# Existing resources (provisioned by infra/main.bicep)
FOUNDRY_ACCOUNT="ai-46j7v4rjni5qw"
SEARCH_SERVICE="search-46j7v4rjni5qw"
FOUNDRY_ENDPOINT="https://ai-46j7v4rjni5qw.cognitiveservices.azure.com/"
SEARCH_ENDPOINT="https://search-46j7v4rjni5qw.search.windows.net"
ACS_COGNITIVE_ENDPOINT="https://ai-46j7v4rjni5qw.cognitiveservices.azure.com/"
ACS_RESOURCE="acs-ccad-itsd-dev"

FOUNDRY_MODEL="gpt-4o"
SEARCH_INDEX="itsd-kb"

# ACR (created if missing). Must be globally unique, lowercase alphanumeric.
ACR_NAME="ccaditsdacr$(echo "$SUBSCRIPTION_ID" | tr -d '-' | cut -c1-6)"
IMAGE_NAME="ccad-itsd-agent"
IMAGE_TAG="latest"

# ----------------------------------------------------------------------------
# Pre-flight
# ----------------------------------------------------------------------------
if [[ -z "${ACS_CONNECTION_STRING:-}" ]]; then
  echo "ERROR: ACS_CONNECTION_STRING is not set."
  echo "  export ACS_CONNECTION_STRING='endpoint=https://...;accesskey=...'"
  exit 1
fi

echo "==> Setting subscription"
az account set --subscription "$SUBSCRIPTION_ID"

# ----------------------------------------------------------------------------
# 1. Container Registry + image build (ACR builds remotely — no local Docker)
# ----------------------------------------------------------------------------
echo "==> Ensuring ACR: $ACR_NAME"
if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  az acr create \
    --name "$ACR_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Basic \
    --admin-enabled true \
    -o none
fi

echo "==> Building image in ACR (context = repo root, uses ./Dockerfile)"
az acr build \
  --registry "$ACR_NAME" \
  --image "${IMAGE_NAME}:${IMAGE_TAG}" \
  --file Dockerfile \
  . \
  -o none

ACR_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)
CONTAINER_IMAGE="${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

# ----------------------------------------------------------------------------
# 2. App Insights connection string (best effort)
# ----------------------------------------------------------------------------
APPINSIGHTS_CONN=$(az monitor app-insights component show \
  --resource-group "$RESOURCE_GROUP" \
  --query "[0].connectionString" -o tsv 2>/dev/null || echo "")

# ----------------------------------------------------------------------------
# 3. Deploy Container App (Bicep) — env, MI, role assignments, ACS callback wiring
# ----------------------------------------------------------------------------
echo "==> Deploying Container App via Bicep"
DEPLOY_OUTPUT=$(az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/app.bicep \
  --parameters \
      location="$LOCATION" \
      baseName="$BASE_NAME" \
      containerImage="$CONTAINER_IMAGE" \
      acrServer="$ACR_SERVER" \
      acrUsername="$ACR_USERNAME" \
      acrPassword="$ACR_PASSWORD" \
      foundryAccountName="$FOUNDRY_ACCOUNT" \
      searchServiceName="$SEARCH_SERVICE" \
      foundryEndpoint="$FOUNDRY_ENDPOINT" \
      foundryModel="$FOUNDRY_MODEL" \
      searchEndpoint="$SEARCH_ENDPOINT" \
      searchIndexName="$SEARCH_INDEX" \
      acsCognitiveServicesEndpoint="$ACS_COGNITIVE_ENDPOINT" \
      acsConnectionString="$ACS_CONNECTION_STRING" \
      appInsightsConnectionString="$APPINSIGHTS_CONN" \
  --query properties.outputs -o json)

APP_URL=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json;print(json.load(sys.stdin)['appUrl']['value'])")
EVENTGRID_WEBHOOK=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys,json;print(json.load(sys.stdin)['eventGridWebhook']['value'])")

# ----------------------------------------------------------------------------
# 4. Point ACS Event Grid subscription at the new public endpoint
# ----------------------------------------------------------------------------
echo "==> Updating Event Grid webhook -> $EVENTGRID_WEBHOOK"
ACS_RESOURCE_ID="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Communication/CommunicationServices/${ACS_RESOURCE}"
if az eventgrid event-subscription show --name incoming-call-webhook --source-resource-id "$ACS_RESOURCE_ID" >/dev/null 2>&1; then
  az eventgrid event-subscription update \
    --name incoming-call-webhook \
    --source-resource-id "$ACS_RESOURCE_ID" \
    --endpoint "$EVENTGRID_WEBHOOK" \
    -o none
else
  az eventgrid event-subscription create \
    --name incoming-call-webhook \
    --source-resource-id "$ACS_RESOURCE_ID" \
    --endpoint "$EVENTGRID_WEBHOOK" \
    --included-event-types Microsoft.Communication.IncomingCall \
    -o none
fi

# ----------------------------------------------------------------------------
# Done
# ----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo " Deployment complete."
echo "   App URL:           $APP_URL"
echo "   Health:            $APP_URL/health"
echo "   Event Grid hook:   $EVENTGRID_WEBHOOK"
echo ""
echo " Test chat:"
echo "   curl -X POST $APP_URL/chat -H 'Content-Type: application/json' \\"
echo "        -d '{\"message\":\"How do I reset my password?\"}'"
echo ""
echo " Then call your ACS phone number to test the voice experience."
echo "============================================================"
