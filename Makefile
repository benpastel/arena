.PHONY: lint
lint:
	cd .. && mypy -p arena
	black .

.PHONY: test
test: lint
	pytest .