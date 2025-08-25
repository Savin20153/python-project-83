install:
	uv sync

uninstall:
	uv tool uninstall hexlet-code
	
build:
	./build.sh

package-install:
	uv tool install dist/*.whl
	
dev:
	uv run flask --debug --app page_analyzer:app run

lint:
	uv run ruff check page_analyzer

lint-fix:
	uv run ruff check page_analyzer --fix

PORT ?= 8000
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app