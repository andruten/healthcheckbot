COMPOSE := docker compose
APP := healthcheckbot
DEV := dev
DB := db

.PHONY: check_env up up_build run down restart build logs ps bash \
	migrate upgrade mysql build_dev test lint lint_check \
	format format_check

check_env:
ifeq ("$(wildcard .env)","")
	cp .env.example .env
endif

up: check_env
	@$(COMPOSE) up -d

up_build: check_env
	@$(COMPOSE) up -d --build

run: check_env
	@$(COMPOSE) up --build

down:
	@$(COMPOSE) down

restart:
	@$(COMPOSE) restart $(APP)

build:
	@$(COMPOSE) build

logs:
	@$(COMPOSE) logs -f $(APP)

ps:
	@$(COMPOSE) ps

bash: check_env build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) bash

migrate:
	@$(COMPOSE) exec $(APP) aerich migrate

upgrade:
	@$(COMPOSE) exec $(APP) aerich upgrade

mysql:
	@$(COMPOSE) exec $(DB) mysql -uhealthchecker -phealthchecker healthchecker

build_dev: check_env
	@$(COMPOSE) build $(DEV)

test: build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) python -m pytest tests/

lint: build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) ruff check --fix --show-fixes

lint_check: build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) ruff check --show-fixes

format: build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) ruff format

format_check: build_dev
	@$(COMPOSE) run --rm --no-deps $(DEV) ruff format --check
