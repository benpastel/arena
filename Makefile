.PHONY: lint
lint:
	black .
	pyflakes .
	mypy -p server


.PHONY: test
test: lint
	pytest . -vv


.PHONY: run
run: lint
	cd .. && python3 -m arena.game


.PHONY: run-client
run-client:
	cd docs && python3 -m http.server 8000


.PHONY: run-server
run-server: lint
	python3 -m server.app