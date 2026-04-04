.PHONY: serve test lint install

install:
	pip install -r requirements.txt

serve:
	uvicorn service.app:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

lint:
	ruff check service/ tests/
