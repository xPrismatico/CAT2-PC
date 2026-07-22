.PHONY: install lint format run test dashboard

ENV_NAME := gamescout

install:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

lint:
	flake8 gamescout app tests

format:
	black gamescout app tests

run:
	python -m gamescout.main

test:
	pytest -v

dashboard:
	python -m streamlit run app/dashboard.py