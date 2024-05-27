.PHONY: lock
lock:
	pip freeze -r requirements/base.in | grep -vFxf requirements/dev.txt > requirements/base.txt

.PHONY: lock-dev
lock-dev:
	pip freeze -r requirements/dev.in | grep -vFxf requirements/base.txt > requirements/dev.txt

.PHONY: reformat
reformat:
	ruff check . --fix
	black .

.PHONY: lint
lint:
	ruff check . --no-fix
	black . --check