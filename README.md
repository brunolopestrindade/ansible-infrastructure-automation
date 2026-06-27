# Ansible Infrastructure Automation

[![CI](https://github.com/brunolopestrindade/ansible-infrastructure-automation/actions/workflows/lint.yml/badge.svg)](https://github.com/brunolopestrindade/ansible-infrastructure-automation/actions/workflows/lint.yml)
[![Ansible](https://img.shields.io/badge/Ansible-2.15+-EE0000?logo=ansible&logoColor=white)](https://docs.ansible.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/Platform-Ubuntu%2022.04%20%7C%20RHEL%208%2F9-blue)](https://ubuntu.com)

> **Production-grade Ansible playbooks for configuration management, multi-environment deployment, and infrastructure standardisation across Linux environments.**  
> Built from real-world operations at enterprise scale — eliminating manual configuration drift across 50+ servers and reducing deployment time from hours to minutes.

---

## The Problem This Solves

Managing infrastructure across multiple environments without automation leads to:

- **Configuration drift** — servers diverge silently over time, causing "works on staging, fails on prod" incidents
- **Tribal knowledge** — only one person knows how to configure a service correctly
- **Slow recovery** — rebuilding a failed server manually takes hours
- **Audit gaps** — no record of who changed what, when, and why

This repository implements **idempotent, version-controlled infrastructure** that eliminates all four problems. Every role can be applied repeatedly with zero side effects.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Control Node                         │
│              (Ansible + Python scripts)                 │
└───────────┬─────────────────────────────────────────────┘
            │ SSH (key-based, no passwords)
    ┌───────┴────────────────────────────────┐
    │                                        │
    ▼                                        ▼
┌──────────────┐                    ┌───────────────────┐
│  Production  │                    │     Staging        │
│  Inventory   │                    │     Inventory      │
├──────────────┤                    ├───────────────────┤
│ webservers   │                    │ webservers        │
│ databases    │                    │ databases         │
│ monitoring   │                    │ monitoring        │
└──────────────┘                    └───────────────────┘
```

**Roles applied per group:**

| Group | Roles |
|---|---|
| All servers | `common`, `security-hardening` |
| Web servers | `common`, `nginx`, `security-hardening` |
| Databases | `common`, `mysql-ha`, `security-hardening` |
| Monitoring | `common`, `elk-stack`, `security-hardening` |

---

## Repository Structure

```
ansible-infrastructure-automation/
│
├── playbooks/
│   ├── site.yml                  # Master playbook — runs all roles
│   ├── site/
│   │   ├── webservers.yml        # Nginx + app config
│   │   └── full-deploy.yml       # Complete environment deploy
│   ├── database/
│   │   ├── mysql-ha.yml          # MySQL high-availability setup
│   │   ├── backup.yml            # Automated DB backup playbook
│   │   └── archiving.yml         # Data retention and archiving
│   ├── monitoring/
│   │   ├── elk-stack.yml         # ELK Stack deployment
│   │   └── dashboards.yml        # Kibana dashboard provisioning
│   └── security/
│       └── hardening.yml         # CIS Benchmark hardening
│
├── roles/
│   ├── common/                   # Base config for all servers
│   ├── elk-stack/                # Elasticsearch + Logstash + Kibana
│   ├── mysql-ha/                 # MySQL with replication
│   ├── nginx/                    # Nginx reverse proxy
│   └── security-hardening/       # SSH, firewall, fail2ban
│
├── inventory/
│   ├── production/
│   │   ├── hosts.yml             # Production hosts (vault-encrypted IPs)
│   │   └── group_vars/
│   └── staging/
│       ├── hosts.yml
│       └── group_vars/
│
├── group_vars/
│   ├── all/
│   │   ├── vars.yml              # Shared variables
│   │   └── vault.yml             # Encrypted secrets (ansible-vault)
│   ├── webservers/vars.yml
│   ├── databases/vars.yml
│   └── monitoring/vars.yml
│
├── scripts/
│   └── python/
│       ├── inventory_report.py   # Dynamic inventory health report
│       ├── log_analyzer.py       # Post-deploy log analysis
│       └── drift_detector.py     # Detect configuration drift
│
├── docs/
│   ├── ROLES.md                  # Detailed role documentation
│   ├── VAULT.md                  # How to manage secrets
│   ├── RUNBOOKS.md               # Operational runbooks
│   └── diagrams/
│       └── architecture.png
│
├── .github/
│   └── workflows/
│       ├── lint.yml              # ansible-lint + yamllint on every PR
│       └── molecule.yml          # Molecule role testing
│
├── ansible.cfg                   # Ansible configuration
├── requirements.yml              # Galaxy roles and collections
└── Makefile                      # Common commands
```

---

## Quick Start

### Prerequisites

```bash
# Python 3.11+ and pip
python3 --version

# Install Ansible and dependencies
pip install -r requirements.txt

# Install required Galaxy collections
ansible-galaxy collection install -r requirements.yml
```

### Run the full site playbook (staging)

```bash
# Syntax check first — always
ansible-playbook -i inventory/staging playbooks/site.yml --syntax-check

# Dry run (check mode)
ansible-playbook -i inventory/staging playbooks/site.yml --check --diff

# Apply
ansible-playbook -i inventory/staging playbooks/site.yml
```

### Run a specific role against production

```bash
# Deploy ELK Stack to monitoring group
ansible-playbook -i inventory/production playbooks/monitoring/elk-stack.yml \
  --limit monitoring \
  --ask-vault-pass \
  --tags "install,configure"
```

### Run security hardening only

```bash
ansible-playbook -i inventory/production playbooks/security/hardening.yml \
  --ask-vault-pass \
  --check   # Always dry-run hardening first
```

---

## Roles

### `common`
Applied to every server. Sets the baseline:
- NTP synchronisation
- Timezone configuration (`Europe/Lisbon` default, overridable)
- Package management (unattended-upgrades, essential tools)
- User and SSH key management
- `/etc/hosts` standardisation

### `security-hardening`
Implements CIS Benchmark Level 1 controls:
- SSH hardening (disable root login, password auth, set ciphers)
- `fail2ban` configuration with custom jail rules
- UFW/firewalld rules per group
- Audit logging (`auditd`)
- Kernel parameter hardening via `sysctl`

### `elk-stack`
Deploys the full observability stack used at PrimeIT:
- **Elasticsearch** — single-node or multi-node cluster, ILM policies
- **Logstash** — pipelines for syslog, application logs, database slow queries
- **Kibana** — with pre-built dashboards for infrastructure monitoring
- Filebeat agent deployment to all managed servers
- Log retention policies (configurable, default 30 days)

### `mysql-ha`
High-availability MySQL setup:
- Primary/replica replication (tested with MySQL 8.0)
- Automated backup via cron (compressed, timestamped, retention-aware)
- Slow query log enabled and shipped to ELK
- Performance tuning via `my.cnf` templates (InnoDB buffer pool, connections)
- Health-check scripts for monitoring integration

### `nginx`
Reverse proxy configuration:
- Virtual host templates (Jinja2)
- SSL termination with Let's Encrypt integration
- Security headers (HSTS, CSP, X-Frame-Options)
- Access log format optimised for Logstash parsing

---

## Secrets Management

All secrets are managed with **Ansible Vault**. No plaintext credentials anywhere in this repository.

```bash
# Create/edit vault file
ansible-vault create group_vars/all/vault.yml
ansible-vault edit group_vars/all/vault.yml

# Encrypt a single value
ansible-vault encrypt_string 'my_secret_password' --name 'db_password'

# Run playbook with vault
ansible-playbook site.yml --ask-vault-pass
# or use a vault password file (for CI/CD):
ansible-playbook site.yml --vault-password-file ~/.vault_pass
```

See [`docs/VAULT.md`](docs/VAULT.md) for the full secrets management workflow.

---

## Python Utilities

### `inventory_report.py`
Generates a health report of all managed hosts — uptime, disk usage, last successful run, pending updates.

```bash
python3 scripts/python/inventory_report.py \
  --inventory inventory/production \
  --output reports/health-$(date +%Y%m%d).html
```

### `drift_detector.py`
Compares current server state against the expected state defined in the playbooks. Alerts on any divergence.

```bash
python3 scripts/python/drift_detector.py \
  --inventory inventory/production \
  --threshold 5  # Alert if more than 5 tasks would change
```

### `log_analyzer.py`
Post-deployment log analysis: queries Elasticsearch for errors in the 10 minutes after a deploy, summarises them, and exits non-zero if error rate spikes — enabling automated rollback in CI/CD pipelines.

```bash
python3 scripts/python/log_analyzer.py \
  --es-host https://elk.internal:9200 \
  --lookback 10m \
  --error-threshold 0.01  # Fail if >1% error rate
```

---

## CI/CD Integration

Every pull request runs:

1. `yamllint` — YAML syntax validation
2. `ansible-lint` — Ansible best practices enforcement
3. `molecule test` — Role testing with Docker containers

```yaml
# .github/workflows/lint.yml (simplified)
- name: Run ansible-lint
  run: ansible-lint playbooks/site.yml

- name: Run molecule tests
  run: |
    cd roles/elk-stack
    molecule test
```

---

## Real-World Impact

These playbooks were developed and refined through production operations:

| Outcome | Detail |
|---|---|
| Configuration drift eliminated | Idempotent runs detect and correct drift on every execution |
| Deployment time | From ~3 hours manual → ~18 minutes automated |
| Incidents reduced | Standardised config removed a class of "snowflake server" failures |
| Onboarding | New servers reach production-ready state in one playbook run |

---

## Makefile Commands

```bash
make lint          # Run yamllint + ansible-lint
make test          # Run molecule tests for all roles
make check-prod    # Dry-run site.yml against production
make deploy-staging # Apply site.yml to staging
make vault-edit    # Edit the encrypted vault file
make inventory-report # Generate HTML health report
```

---

## Requirements

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Ansible | 2.15+ |
| ansible-lint | 6.x |
| molecule | 6.x |

```bash
pip install ansible==9.* ansible-lint molecule molecule-docker
```

---

## Contributing

1. Branch from `main` — `git checkout -b feat/role-name`
2. Always run `make lint` before committing
3. Add or update molecule tests for any role changes
4. Update `docs/ROLES.md` if the role interface changes
5. Open a PR — CI must be green before merge

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

**Bruno Lopes Trindade**  
Senior DevOps & Cloud Engineer | 20+ years in Linux infrastructure and automation  
[LinkedIn](https://www.linkedin.com/in/bruno-lopes-trindade) · [GitHub](https://github.com/brunolopestrindade)

> *"Infrastructure that requires a human to configure it is infrastructure that will eventually fail at 3am."*
