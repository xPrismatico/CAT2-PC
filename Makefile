.PHONY: install lint format run test

ENV_NAME := gamescout

install:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

lint:
	flake8 gamescout tests

format:
	black gamescout tests

run:
	python -m gamescout.main

test:
	pytest -v
