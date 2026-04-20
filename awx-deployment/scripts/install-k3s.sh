#!/bin/bash
# AWX Production - K3s Installation Script
# This script installs a lightweight Kubernetes cluster for AWX

set -euo pipefail

echo "=== AWX Production: Installing K3s ==="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# System requirements check
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [[ $TOTAL_MEM -lt 8 ]]; then
    echo "WARNING: Minimum 8 GB RAM recommended. Found: ${TOTAL_MEM} GB"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install K3s
curl -sfL https://get.k3s.io | sh -s - \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --disable servicelb

# Wait for K3s to be ready
echo "Waiting for K3s to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=120s

# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

echo "Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s

echo ""
echo "=== K3s Installation Complete ==="
echo "Kubeconfig: /etc/rancher/k3s/k3s.yaml"
echo "Next step: Run ./deploy-awx.sh"
