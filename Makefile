.PHONY: up down logs build test lint fmt clean

up:            ## Build and start the full stack
	docker compose up --build

down:          ## Stop the stack
	docker compose down

logs:          ## Tail service logs
	docker compose logs -f

build:         ## Build images without starting
	docker compose build

test:          ## Run backend tests inside the backend image
	docker compose run --rm backend pytest

lint:          ## Lint the backend
	docker compose run --rm backend ruff check .

fmt:           ## Auto-fix backend lint issues
	cd backend && ruff check --fix . && ruff format .

clean:         ## Remove containers and the data volume
	docker compose down -v
