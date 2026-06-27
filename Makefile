.PHONY: lint test check-staging check-prod deploy-staging vault-edit inventory-report drift-check

INVENTORY_STAGING  := inventory/staging
INVENTORY_PROD     := inventory/production
PLAYBOOK           := playbooks/site.yml

lint:
	yamllint .
	ansible-lint $(PLAYBOOK)

test:
	@for role in common security-hardening elk-stack; do \
		echo "==> Testing role: $$role"; \
		cd roles/$$role && molecule test && cd ../..; \
	done

check-staging:
	ansible-playbook -i $(INVENTORY_STAGING) $(PLAYBOOK) --check --diff

check-prod:
	ansible-playbook -i $(INVENTORY_PROD) $(PLAYBOOK) --check --diff --ask-vault-pass

deploy-staging:
	ansible-playbook -i $(INVENTORY_STAGING) $(PLAYBOOK)

deploy-prod:
	@echo "Production deploy — vault password required"
	ansible-playbook -i $(INVENTORY_PROD) $(PLAYBOOK) --ask-vault-pass

vault-edit:
	ansible-vault edit group_vars/all/vault.yml

inventory-report:
	python3 scripts/python/inventory_report.py \
		--inventory $(INVENTORY_PROD) \
		--output reports/health-$(shell date +%Y%m%d).html

drift-check:
	python3 scripts/python/drift_detector.py \
		--inventory $(INVENTORY_PROD) \
		--threshold 5
