# AWX Production Deployment Guide — 150 Servers

## Overview

This guide deploys AWX (open-source Ansible Tower) to manage your 150-server infrastructure.

**Savings:** ~$14,000/year vs Ansible Tower licensing.

---

## Architecture

```
                    +-------------------+
                    |   Load Balancer   |
                    |     (Nginx)       |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+         +---------v-------+
     |  AWX Web (x2)   |         |  AWX Web (x2)   |
     |  2vCPU / 4GB    |         |  2vCPU / 4GB    |
     +--------+---------+         +--------+--------+
              |                             |
     +--------v-----------------------------v--------+
     |           AWX Task Runners (x2)               |
     |            4vCPU / 8GB each                   |
     |     [Runs playbooks on 150 servers]           |
     +------------------------+----------------------+
                              |
              +---------------+---------------+
              |               |               |
     +--------v---+  +--------v---+  +--------v---+
     | PostgreSQL  |  |   Redis    |  | Receptor   |
     | 4GB/100GB   |  |  2GB/10GB  |  |  (mesh)    |
     +-------------+  +------------+  +------------+
                              |
         +--------------------+--------------------+
         |          |          |         |         |
    [30 web]  [50 app]  [15 db]  [25 worker]  [30 other]
```

## Hardware Requirements

| Component | CPU | RAM | Storage | Monthly Cost |
|-----------|-----|-----|---------|-------------|
| AWX Web x2 | 2 vCPU | 4 GB | 20 GB | ~$60 |
| AWX Task x2 | 4 vCPU | 8 GB | 40 GB | ~$120 |
| PostgreSQL | 2 vCPU | 4 GB | 100 GB | ~$40 |
| Redis | 1 vCPU | 2 GB | 10 GB | ~$15 |
| **Total** | | | | **~$235/mo** |

---

## Deployment Steps

### Prerequisites

- Linux server (Ubuntu 22.04 / RHEL 9 recommended)
- Minimum 16 GB RAM, 4 vCPU on the AWX host
- Network access to all 150 managed servers (SSH port 22)
- DNS record pointing to AWX server (e.g., awx.yourdomain.com)
- TLS certificate for HTTPS

### Step 1: Install Kubernetes (K3s)

```bash
chmod +x scripts/install-k3s.sh
sudo ./scripts/install-k3s.sh
```

### Step 2: Deploy AWX

```bash
chmod +x scripts/deploy-awx.sh
./scripts/deploy-awx.sh
```

### Step 3: Configure TLS

1. Edit `manifests/04-ingress-tls.yaml`
2. Replace `REPLACE_WITH_BASE64_ENCODED_CERT` with your cert:
   ```bash
   cat your-cert.crt | base64 -w0
   cat your-key.key | base64 -w0
   ```
3. Apply: `kubectl apply -f manifests/04-ingress-tls.yaml`

### Step 4: Login to AWX

1. Open https://awx.yourdomain.com
2. Username: `admin`
3. Password: Get with:
   ```bash
   kubectl -n awx get secret awx-production-admin-password \
       -o jsonpath="{.data.password}" | base64 --decode
   ```

---

## Post-Deployment Configuration

### 1. Add Your 150 Servers

In AWX UI:
1. **Inventories** → Add → Name: "Production-150"
2. **Sources** → Add → Source: "Sourced from a Project"
3. Point to `inventory/production-inventory.yaml`

Or import via CLI:
```bash
awx-manage inventory_import --source=inventory/production-inventory.yaml \
    --inventory-name="Production-150"
```

### 2. Configure LDAP Authentication

In AWX UI → Settings → Authentication → LDAP:

```
LDAP Server URI: ldaps://ldap.yourdomain.com:636
LDAP Bind DN: cn=awx-service,ou=services,dc=yourdomain,dc=com
LDAP User Search: ou=users,dc=yourdomain,dc=com
LDAP Group Search: ou=groups,dc=yourdomain,dc=com
```

### 3. Set Up Credentials

Create these credential types in AWX:
- **Machine** — SSH keys for your 150 servers
- **Source Control** — Git access for playbook repos
- **Vault** — HashiCorp Vault token (if using)
- **Cloud** — AWS/Azure/GCP (if applicable)

### 4. Organize with RBAC

Suggested roles:
| Role | Access |
|------|--------|
| Admin | Full access to all resources |
| Ops Engineer | Execute jobs, view all inventories |
| Developer | Execute jobs on dev/staging only |
| Viewer | Read-only dashboard access |

### 5. Set Up Notifications

Configure in AWX → Notifications:
- **Slack** — Job failures and critical alerts
- **Email** — Daily job summary reports
- **Webhook** — Integration with monitoring (PagerDuty, OpsGenie)

---

## Server Grouping Strategy (150 Servers)

| Group | Count | Purpose |
|-------|-------|--------|
| webservers | 30 | Nginx/Apache front-end |
| appservers | 50 | Application backends |
| databases | 15 | PostgreSQL/MySQL |
| cache_servers | 10 | Redis/Memcached |
| monitoring | 5 | Prometheus/Grafana |
| loadbalancers | 5 | HAProxy/Nginx LB |
| workers | 25 | Background job processors |
| storage | 10 | NFS/object storage |
| **Total** | **150** | |

---

## Security Hardening

### AWX Platform Security

- [x] HTTPS enforced (TLS 1.2+)
- [x] Session cookies marked Secure + HttpOnly
- [x] CSRF protection enabled
- [x] Session timeout: 30 minutes
- [x] Max 3 sessions per user
- [ ] LDAP/SSO authentication (configure post-deploy)
- [ ] Network policies applied (manifests/04-ingress-tls.yaml)
- [ ] Backup CronJob active (manifests/05-backup-cronjob.yaml)

### Managed Server Security

- Use SSH keys only (no passwords)
- Dedicated `deploy` user with sudo on all 150 servers
- Firewall rules: only allow SSH from AWX IP
- Regular credential rotation via AWX Credential Type

---

## Maintenance

### Daily Backup (Automated)

The `05-backup-cronjob.yaml` runs daily at 2:00 AM:
- PostgreSQL full dump
- Retains 7 days of backups
- Storage: 50 GB PVC

### Health Checks

```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

### Upgrading AWX

```bash
# Update operator image tag in 01-awx-operator.yaml
kubectl -n awx set image deployment/awx-operator-controller-manager \
    awx-manager=quay.io/ansible/awx-operator:NEW_VERSION

# AWX instance upgrades automatically after operator update
```

---

## Troubleshooting

| Issue | Command |
|-------|--------|
| Pods not starting | `kubectl -n awx describe pods` |
| Check AWX logs | `kubectl -n awx logs -l app.kubernetes.io/name=awx-production -f` |
| Database connection | `kubectl -n awx exec -it deploy/awx-production-postgres -- psql` |
| Restart AWX | `kubectl -n awx rollout restart deployment awx-production-web` |
| Check disk usage | `kubectl -n awx exec -it deploy/awx-production-postgres -- df -h` |
| Reset admin password | `kubectl -n awx exec -it deploy/awx-production-web -- awx-manage changepassword admin` |

---

## File Structure

```
awx-deployment/
├── docs/
│   └── DEPLOYMENT_GUIDE.md          # This file
├── manifests/
│   ├── 00-namespace.yaml            # AWX namespace
│   ├── 01-awx-operator.yaml         # AWX Operator deployment
│   ├── 02-postgres-pvc.yaml         # Database storage
│   ├── 03-awx-production.yaml       # Main AWX instance (150-server config)
│   ├── 04-ingress-tls.yaml          # TLS + Network Policy
│   └── 05-backup-cronjob.yaml       # Automated daily backups
├── inventory/
│   ├── production-inventory.yaml    # 150 server inventory template
│   └── group_vars/
│       └── all.yaml                 # Global variables
└── scripts/
    ├── install-k3s.sh               # Kubernetes installation
    ├── deploy-awx.sh                # One-command AWX deployment
    └── health-check.sh              # Production health monitoring
```
