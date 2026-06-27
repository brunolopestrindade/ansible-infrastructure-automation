# Operational Runbooks

Quick-reference for the most common operational tasks.

---

## Add a new server to the managed fleet

```bash
# 1. Add host to the correct inventory group
vim inventory/production/hosts.yml

# 2. Add vault variable for the IP
ansible-vault edit group_vars/all/vault.yml

# 3. Test connectivity
ansible new-host -i inventory/production -m ping

# 4. Apply baseline (common + security-hardening)
ansible-playbook -i inventory/production playbooks/site.yml \
  --limit new-host \
  --ask-vault-pass

# 5. Verify — run again in check mode, expect 0 changes
ansible-playbook -i inventory/production playbooks/site.yml \
  --limit new-host --check --ask-vault-pass
```

---

## Rotate SSH keys

```bash
# 1. Add the new public key to vault
ansible-vault edit group_vars/all/vault.yml
# Append to ops_ssh_public_keys list

# 2. Apply common role to push new key
ansible-playbook -i inventory/production playbooks/site.yml \
  --tags ssh --ask-vault-pass

# 3. Verify access with new key, then remove old key from vault

# 4. Apply again to remove old key
ansible-playbook -i inventory/production playbooks/site.yml \
  --tags ssh --ask-vault-pass
```

---

## Emergency: ELK Stack not receiving logs

```bash
# Check Filebeat status on a source server
ansible webservers -i inventory/production \
  -m systemd -a "name=filebeat" --ask-vault-pass

# Restart Filebeat on all servers
ansible all -i inventory/production \
  -m systemd -a "name=filebeat state=restarted" \
  --become --ask-vault-pass

# Check Elasticsearch cluster health
ansible monitoring -i inventory/production \
  -m uri -a "url=http://localhost:9200/_cluster/health" \
  --ask-vault-pass
```

---

## Manual database backup before maintenance

```bash
ansible-playbook -i inventory/production playbooks/database/backup.yml \
  --ask-vault-pass

# Verify backup was created
ansible databases -i inventory/production \
  -m find -a "paths=/var/backups/mysql patterns=*.sql.gz age=-10m" \
  --ask-vault-pass
```

---

## Check configuration drift before a change window

```bash
make drift-check

# Or manually:
ansible-playbook -i inventory/production playbooks/site.yml \
  --check --diff --ask-vault-pass 2>&1 | tee /tmp/drift-$(date +%Y%m%d).log
```
