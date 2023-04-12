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
	cd client && python3 -m http.server 8000
	# find external IP address with: `ifconfig | rg en0 --after-context=6 | rg inet`



.PHONY: run-server
run-server: lint
	cd .. && python3 -m arena.server.app