DOCKER := docker
CURRENT_DIR := $(shell pwd)
IMAGE_NAME := healthcheckbot

.PHONY:

check_env:
ifeq ("$(wildcard .env)","")
	cp env.sample .env
endif

run: check_env build
	@$(DOCKER) run --name $(IMAGE_NAME) --restart on-failure:3 --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway $(IMAGE_NAME):latest

run_detached: check_env build
	@$(DOCKER) run -d --name $(IMAGE_NAME) --restart on-failure:3 --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway -ti $(IMAGE_NAME):latest

run_dev: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app --add-host=host.docker.internal:host-gateway -ti $(IMAGE_NAME):latest

build:
	@$(DOCKER) build . -t $(IMAGE_NAME):latest

build_dev: check_env
	@$(DOCKER) build --build-arg requirements=dev . -t $(IMAGE_NAME):latest

bash: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app -ti $(IMAGE_NAME):latest bash

lint: check_env build_dev
	@$(DOCKER) run --rm --env-file .env $(IMAGE_NAME):latest flake8 .

test: check_env build_dev
	@$(DOCKER) run --rm --env-file .env $(IMAGE_NAME):latest python -m pytest .

coverage: check_env build_dev
	@$(DOCKER) run --rm --env-file .env -v $(CURRENT_DIR):/opt/app $(IMAGE_NAME):latest python -m pytest --cov-report html
