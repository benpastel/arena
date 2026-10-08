.PHONY: lint
lint:
	uv run black .
	uv run pyflakes server test
	uv run mypy -p server


.PHONY: test
test: lint
	uv run pytest . -vv


.PHONY: run-client
run-client:
	cd docs && uv run python -m http.server 8000


.PHONY: run-server
run-server: lint
	uv run python -m server.app


# render installs from requirements.txt; regenerate it after changing dependencies
requirements.txt: pyproject.toml uv.lock
	uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt
