.PHONY: install test coverage lint format check clean dist

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

coverage:
	python -m pytest -q --cov=subcue --cov-report=term-missing --cov-fail-under=95

lint:
	python -m ruff check src tests examples scripts
	python -m ruff format --check src tests examples scripts

format:
	python -m ruff check --fix src tests examples scripts
	python -m ruff format src tests examples scripts

check: lint coverage

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .tox .coverage coverage.xml htmlcov

dist: clean
	python -m build
