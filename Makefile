.PHONY: lint
lint:
	black .
	pyflakes .
	cd .. && mypy -p arena


.PHONY: test
test: lint
	pytest . -vv

.PHONY: run
run: test
	cd .. && python -m arena.game