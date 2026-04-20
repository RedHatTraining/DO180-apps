#!/bin/bash
# AWX Production Deployment Script
# Deploys AWX on Kubernetes for managing 150 servers

set -euo pipefail

MANIFESTS_DIR="$(dirname "$0")/../manifests"

echo "=== AWX Production Deployment ==="
echo "Target: 150 server infrastructure"
echo ""

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not found. Install Kubernetes first."
    echo "Run: ./install-k3s.sh"
    exit 1
fi

# Verify cluster is ready
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster."
    exit 1
fi

echo "[1/5] Creating namespace..."
kubectl apply -f "${MANIFESTS_DIR}/00-namespace.yaml"

echo "[2/5] Deploying AWX Operator..."
kubectl apply -f "${MANIFESTS_DIR}/01-awx-operator.yaml"

echo "Waiting for AWX Operator to be ready..."
kubectl wait --namespace awx \
    --for=condition=available deployment/awx-operator-controller-manager \
    --timeout=300s

echo "[3/5] Creating persistent storage..."
kubectl apply -f "${MANIFESTS_DIR}/02-postgres-pvc.yaml"

echo "[4/5] Deploying AWX instance..."
kubectl apply -f "${MANIFESTS_DIR}/03-awx-production.yaml"

echo "Waiting for AWX to be ready (this may take 5-10 minutes)..."
echo "You can monitor progress with: kubectl -n awx get pods -w"

# Wait for AWX web pod to be ready
for i in {1..60}; do
    if kubectl -n awx get pods | grep -q "awx-production-web.*Running"; then
        break
    fi
    echo "  Still deploying... (${i}/60)"
    sleep 10
done

echo "[5/5] Setting up backup schedule..."
kubectl apply -f "${MANIFESTS_DIR}/05-backup-cronjob.yaml"

echo ""
echo "=== Deployment Complete ==="
echo ""

# Get admin password
ADMIN_PASSWORD=$(kubectl -n awx get secret awx-production-admin-password \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 --decode)

if [[ -n "$ADMIN_PASSWORD" ]]; then
    echo "AWX Admin Credentials:"
    echo "  Username: admin"
    echo "  Password: ${ADMIN_PASSWORD}"
    echo ""
fi

echo "AWX URL: https://awx.yourdomain.com"
echo ""
echo "Next steps:"
echo "  1. Configure TLS: Update manifests/04-ingress-tls.yaml with your certificates"
echo "  2. Add your 150 servers to the inventory"
echo "  3. Configure LDAP authentication"
echo "  4. Set up credential vaults"
echo "  5. Import playbooks from your Git repositories"
