.PHONY: lock
lock:
	pip freeze -r requirements/base.in | grep -vFxf requirements/dev.txt > requirements/base.txt

.PHONY: update
update:
	pip install -U -r requirements/base.in
	make lock

.PHONY: lock-dev
lock-dev:
	pip freeze -r requirements/dev.in | grep -vFxf requirements/base.txt > requirements/dev.txt

.PHONY: update-dev
update-dev:
	pip install -U -r requirements/dev.in
	make lock-dev

.PHONY: reformat
reformat:
	ruff check . --fix
	black .

.PHONY: lint
lint:
	ruff check . --no-fix
	black . --check

.PHONY: test
test:
	pytest --cov --cov-branch --cov-report=term --cov-report=html  -m 'not pw' tests/

.PHONY: test-pw
test-pw:
	pytest -m pw tests/

.PHONY: audit
audit:
	pip-audit
