.PHONY: help install install-dev test lint format clean container-build container-run container-test

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install         - Install production dependencies"
	@echo "  make install-dev     - Install development dependencies"
	@echo "  make test            - Run tests with coverage"
	@echo "  make lint            - Run linting checks"
	@echo "  make format          - Format code with black and ruff"
	@echo "  make clean           - Clean build and cache files"
	@echo ""
	@echo "Container:"
	@echo "  make container-build - Build container image"
	@echo "  make container-run   - Run container with dry-run"
	@echo "  make container-test  - Test container image"
	@echo "  make container-push  - Push container to registry"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest -v --cov=firstpass --cov-report=term-missing --cov-report=html

lint:
	@echo "Running ruff..."
	ruff check .
	@echo "Running black check..."
	black --check .
	@echo "Running mypy..."
	mypy firstpass --ignore-missing-imports

format:
	@echo "Formatting with black..."
	black .
	@echo "Auto-fixing with ruff..."
	ruff check --fix .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

# Container commands
RUNTIME ?= $(shell command -v podman 2>/dev/null || command -v docker 2>/dev/null)
IMAGE_NAME ?= firstpass-agent
IMAGE_TAG ?= latest

container-build:
	@if [ -z "$(RUNTIME)" ]; then \
		echo "Error: Neither podman nor docker found"; \
		exit 1; \
	fi
	$(RUNTIME) build -t $(IMAGE_NAME):$(IMAGE_TAG) -f Containerfile .

container-run: container-build
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Copy .env.example to .env"; \
		exit 1; \
	fi
	$(RUNTIME) run --rm \
		--env-file .env \
		-v $(PWD)/config.yaml:/app/config.yaml:ro \
		$(IMAGE_NAME):$(IMAGE_TAG) --dry-run

container-test: container-build
	$(RUNTIME) run --rm $(IMAGE_NAME):$(IMAGE_TAG) --help
	@echo "Container test passed!"

container-push: container-build
	@if [ -z "$(REGISTRY)" ]; then \
		echo "Error: REGISTRY not set. Use: make container-push REGISTRY=quay.io/yourorg"; \
		exit 1; \
	fi
	$(RUNTIME) tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	$(RUNTIME) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
