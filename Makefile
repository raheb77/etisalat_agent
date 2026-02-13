backend-run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd backend && pytest

backend-lint:
	@echo "No lint configured"

venv-check:
	@if [ -z "$$VIRTUAL_ENV" ]; then echo "Virtualenv is not active. Please activate your venv and retry."; exit 1; fi

test:
	@cd backend && pytest -q

phase2-smoke:
	@./scripts/phase2_smoke.sh

phase2-validate: venv-check test phase2-smoke
