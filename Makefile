.PHONY: help test test-integration test-addon test-local lint build clean up down logs

help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-integration  - Test integration code"
	@echo "  test-addon        - Test add-on code"
	@echo "  test-local        - Run local tests with docker-compose"
	@echo "  lint              - Lint all code"
	@echo "  build             - Build add-on Docker image"
	@echo "  up                - Start docker-compose services"
	@echo "  down              - Stop docker-compose services"
	@echo "  logs              - View docker-compose logs"
	@echo "  clean             - Clean up test artifacts"

test: lint test-integration test-addon

test-integration:
	@echo "Testing integration..."
	@python3 -m py_compile custom_components/bluetooth_tracker/*.py
	@cd test-utils && python3 test_integration.py

test-addon:
	@echo "Testing add-on..."
	@python3 -m py_compile homeassistant_addon/rootfs/app/*.py

test-local:
	@echo "Starting local test environment..."
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@echo "Tests complete"

lint:
	@echo "Linting integration code..."
	@python3 -m flake8 custom_components/bluetooth_tracker --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@echo "Linting add-on code..."
	@python3 -m flake8 homeassistant_addon/rootfs/app --count --select=E9,F63,F7,F82 --show-source --statistics || true

build:
	@echo "Building add-on..."
	cd homeassistant_addon && docker build -t bluetooth-monitor:latest --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11 .

up:
	@echo "Starting services..."
	docker-compose up -d

down:
	@echo "Stopping services..."
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf test-config/.storage test-config/*.db test-config/*.log
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
