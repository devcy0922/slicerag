.PHONY: run test lint typecheck check

run:
	uvicorn slicerag.main:app --reload --host 0.0.0.0 --port 8095

test:
	pytest

lint:
	ruff check src tests

typecheck:
	mypy src

check: lint typecheck test

