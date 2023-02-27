.PHONY: lint
lint:
	black .
	pyflakes .
	cd .. && mypy -p arena


.PHONY: test
test: lint
	pytest . -vv

.PHONY: run
run: lint
	cd .. && python3 -m arena.game