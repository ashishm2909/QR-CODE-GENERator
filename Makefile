.PHONY: install run clean test cleanup-uploads docker-build docker-run

install:
	pip install -r backend/requirements.txt

run:
	cd backend && python wsgi.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

cleanup-uploads:
	python scripts/cleanup.py

docker-build:
	docker build -t qr-generator .

docker-run:
	docker-compose up -d

test:
	@echo "No tests configured yet."
