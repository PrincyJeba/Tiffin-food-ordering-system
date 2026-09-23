#!/usr/bin/env bash
# One-time setup for Teammate 2. Run this once from Cloud Shell or a machine
# with gcloud installed and authenticated (gcloud auth login).
#
# Usage:
#   PROJECT_ID=your-project-id GITHUB_REPO=your-github-username/food-ordering-system ./gcp-setup.sh

set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID=your-gcp-project-id}"
: "${GITHUB_REPO:?Set GITHUB_REPO=github-username/repo-name}"

REGION="asia-south1"
REPOSITORY="food-ordering"
SERVICE_ACCOUNT="github-actions-deployer"
POOL="github-pool"
PROVIDER="github-provider"

gcloud config set project "$PROJECT_ID"

echo "==> Enabling required APIs (free — you only pay for usage, not for enabling)"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudresourcemanager.googleapis.com

echo "==> Creating Artifact Registry Docker repository"
gcloud artifacts repositories create "$REPOSITORY" \
  --repository-format=docker \
  --location="$REGION" \
  --description="Food ordering system images" || echo "Repository may already exist, continuing."

echo "==> Creating a dedicated service account for GitHub Actions"
gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
  --display-name="GitHub Actions Deployer" || echo "Service account may already exist, continuing."

SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Granting minimum roles needed to build, push, and deploy"
for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="$ROLE" \
    --condition=None
done

echo "==> Setting up Workload Identity Federation (no downloadable key needed)"
gcloud iam workload-identity-pools create "$POOL" \
  --location="global" \
  --display-name="GitHub Actions Pool" || echo "Pool may already exist, continuing."

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --location="global" \
  --workload-identity-pool="$POOL" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" || echo "Provider may already exist, continuing."

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GITHUB_REPO}"

echo ""
echo "================= DONE ================="
echo "Add these as GitHub Actions secrets (repo Settings -> Secrets and variables -> Actions):"
echo ""
echo "GCP_PROJECT_ID     = ${PROJECT_ID}"
echo "WIF_SERVICE_ACCOUNT = ${SA_EMAIL}"
echo "WIF_PROVIDER        = projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
echo "=========================================="
