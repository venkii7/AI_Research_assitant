.PHONY: install dev test lint db-setup clean

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

test:
	pytest tests/ -v --asyncio-mode=auto

lint:
	ruff check . --fix
	ruff format .

db-setup:
	python -c "from services.supabase_client import supabase; print('DB connected')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache
