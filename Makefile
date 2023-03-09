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


.PHONY: serve-http
serve-http:
	cd web && python3 -m http.server

.PHONY: serve-websockets
serve-websockets:
	cd web && python3 -m app