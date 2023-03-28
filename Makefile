DOCKER := docker
CURRENT_DIR := $(shell pwd)

.PHONY:

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

run: check_env build
	@$(DOCKER) run --name healthcheckbot --restart on-failure:3 --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway healthcheckbot:latest

run_detached: check_env build
	@$(DOCKER) run -d --name healthcheckbot --restart on-failure:3 --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway -ti healthcheckbot:latest

run_dev: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway -ti healthcheckbot:latest

build:
	@$(DOCKER) build . -t healthcheckbot:latest

build_dev: check_env
	@$(DOCKER) build --build-arg requirements=dev . -t healthcheckbot:latest

bash: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app -ti healthcheckbot:latest bash

lint: check_env build_dev
	@$(DOCKER) run --rm --env-file .env healthcheckbot:latest flake8 .

test: check_env build_dev
	@$(DOCKER) run --rm --env-file .env healthcheckbot:latest python -m pytest .

coverage: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app healthcheckbot:latest python -m pytest --cov-report html
