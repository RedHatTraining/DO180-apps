#!/bin/bash
# AWX Production Health Check Script
# Run this periodically to verify AWX is healthy

set -euo pipefail

echo "=== AWX Production Health Check ==="
echo "Date: $(date)"
echo ""

ERRORS=0

# Check pods
echo "[Pods Status]"
kubectl -n awx get pods -o wide
echo ""

# Check if all pods are running
NOT_RUNNING=$(kubectl -n awx get pods --no-headers | grep -v "Running\|Completed" | wc -l)
if [[ $NOT_RUNNING -gt 0 ]]; then
    echo "WARNING: ${NOT_RUNNING} pod(s) not in Running state"
    ERRORS=$((ERRORS + 1))
fi

# Check PVC usage
echo "[Storage Status]"
kubectl -n awx get pvc
echo ""

# Check AWX web endpoint
echo "[Web Endpoint]"
AWX_SVC=$(kubectl -n awx get svc awx-production-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
if [[ -n "$AWX_SVC" ]]; then
    HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" "http://${AWX_SVC}:80/api/v2/ping/" 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "200" ]]; then
        echo "  API Status: HEALTHY (HTTP ${HTTP_CODE})"
    else
        echo "  API Status: UNHEALTHY (HTTP ${HTTP_CODE})"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  AWX service not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check recent jobs
echo "[Recent Job Status]"
kubectl -n awx logs -l app.kubernetes.io/component=awx-task --tail=20 2>/dev/null | grep -i "error\|fail" | tail -5 || echo "  No recent errors"
echo ""

# Check resource usage
echo "[Resource Usage]"
kubectl -n awx top pods 2>/dev/null || echo "  Metrics server not available"
echo ""

# Summary
echo "=== Summary ==="
if [[ $ERRORS -eq 0 ]]; then
    echo "Status: ALL HEALTHY"
else
    echo "Status: ${ERRORS} ISSUE(S) DETECTED"
fi
