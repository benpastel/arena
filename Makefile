.PHONY: lint
lint:
	cd .. && mypy -p arena
	black .

.PHONY: test
test: lint
	pytest . -vv

.PHONY: run
run: test
	cd .. && python -m arena.game