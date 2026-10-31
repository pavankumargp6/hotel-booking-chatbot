.PHONY: install test lint sam-validate sam-build clean

install:
	pip install -r requirements.txt -r requirements-dev.txt ruff

test:
	PYTHONPATH=src pytest --cov=src --cov-report=term-missing --cov-fail-under=90

lint:
	ruff check src tests

sam-validate:
	sam validate --lint

sam-build:
	sam build

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov .aws-sam
	find . -type d -name __pycache__ -exec rm -rf {} +
