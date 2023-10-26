#SHELL := bash
#.ONESHELL:
#.SHELLFLAGS := -eu -o pipefail -c
#.DELETE_ON_ERROR:
#MAKEFLAGS += --warn-undefined-variables
#MAKEFLAGS += --no-builtin-rules

up:
	docker-compose up -d
start:
	docker-compose up
down:
	docker-compose down
logs:
	docker-compose logs -f
build:
	docker-compose build

prod-up:
	docker-compose -f production.yml up -d

prod-down:
	docker-compose -f production.yml down

prod-build:
	docker-compose -f production.yml build
prod-logs:
	docker-compose -f production.yml logs -f
