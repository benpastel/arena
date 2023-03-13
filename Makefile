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


.PHONY: run-client
run-client:
	cd client && python3 -m http.server


.PHONY: run-server
run-server: lint
	cd .. && python3 -m arena.server.app