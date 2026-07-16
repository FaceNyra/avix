.PHONY: install lint mypy test migrate up down dev

install:
	uv sync --all-extras

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

mypy:
	uv run mypy src/app

test:
	uv run pytest -q

migrate:
	uv run alembic upgrade head

up:
	docker compose up --build

down:
	docker compose down

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
