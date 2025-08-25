.PHONY: help up down build test lint fmt clean migrate seed grafana logs shell api-shell worker-shell

# Default target
help: ## Show this help message
	@echo "AI Voice Policy Assistant - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Infrastructure
up: ## Start the complete local stack
	@echo "Starting AI Voice Policy Assistant stack..."
	docker-compose -f infra/docker-compose.yml up --build -d
	@echo "Stack started! Access:"
	@echo "  API: http://localhost:8000"
	@echo "  Grafana: http://localhost:3000 (admin/admin)"
	@echo "  Prometheus: http://localhost:9090"

down: ## Stop the local stack
	@echo "Stopping AI Voice Policy Assistant stack..."
	docker-compose -f infra/docker-compose.yml down
	@echo "Stack stopped"

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker-compose -f infra/docker-compose.yml build --no-cache
	@echo "Build complete"

# Development
dev: ## Start in development mode with hot reload
	@echo "Starting development mode..."
	docker-compose -f infra/docker-compose.yml up --build api postgres redis
	@echo "Development stack started!"

test: ## Run tests
	@echo "Running tests..."
	python -m pytest tests/ -v --tb=short

lint: ## Run linting checks
	@echo "Running linting checks..."
	ruff check .
	@echo "Linting complete"

fmt: ## Format code with ruff
	@echo "Formatting code..."
	ruff format .
	@echo "Code formatting complete"

# Database
migrate: ## Run database migrations
	@echo "Running database migrations..."
	docker-compose -f infra/docker-compose.yml exec api alembic upgrade head

migrate-create: ## Create a new migration
	@echo "Creating new migration..."
	@read -p "Enter migration name: " name; \
	docker-compose -f infra/docker-compose.yml exec api alembic revision --autogenerate -m "$$name"

seed: ## Seed the database with sample data
	@echo "Seeding database with sample data..."
	python scripts/ingest_corpus.py scripts/corpus/
	@echo "Database seeded!"

# Monitoring
grafana: ## Open Grafana dashboard
	@echo "Opening Grafana dashboard..."
	open http://localhost:3000
	@echo "Login with admin/admin"

prometheus: ## Open Prometheus metrics
	@echo "Opening Prometheus metrics..."
	open http://localhost:9090

# Logs and debugging
logs: ## Show logs from all services
	docker-compose -f infra/docker-compose.yml logs -f

api-logs: ## Show API service logs
	docker-compose -f infra/docker-compose.yml logs -f api

worker-logs: ## Show worker service logs
	docker-compose -f infra/docker-compose.yml logs -f worker

db-logs: ## Show database logs
	docker-compose -f infra/docker-compose.yml logs -f postgres

# Shell access
shell: ## Access API container shell
	docker-compose -f infra/docker-compose.yml exec api /bin/bash

worker-shell: ## Access worker container shell
	docker-compose -f infra/docker-compose.yml exec worker /bin/bash

db-shell: ## Access database shell
	docker-compose -f infra/docker-compose.yml exec postgres psql -U user -d proxi

redis-shell: ## Access Redis shell
	docker-compose -f infra/docker-compose.yml exec redis redis-cli

# Maintenance
clean: ## Clean up containers, images, and volumes
	@echo "Cleaning up..."
	docker-compose -f infra/docker-compose.yml down -v --rmi all
	docker system prune -f
	@echo "Cleanup complete"

clean-data: ## Clean up data volumes (WARNING: This will delete all data)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose -f infra/docker-compose.yml down -v; \
		docker volume prune -f; \
		echo "Data volumes cleaned!"; \
	else \
		echo "Cleanup cancelled"; \
	fi

# Health checks
health: ## Check system health
	@echo "Checking system health..."
	@curl -s http://localhost:8000/healthz | jq . || echo "API not responding"
	@echo "Checking services..."
	@docker-compose -f infra/docker-compose.yml ps

# Load testing
load-test: ## Run load tests
	@echo "Running load tests..."
	python scripts/load_test.py
	@echo "Load test complete"

# Corpus management
corpus-ingest: ## Ingest documents from scripts/corpus/
	@echo "Ingesting corpus documents..."
	python scripts/ingest_corpus.py scripts/corpus/
	@echo "Corpus ingestion complete"

corpus-reindex: ## Reindex all documents
	@echo "Reindexing corpus..."
	curl -X POST http://localhost:8000/corpus/reindex \
		-H "Authorization: Bearer YOUR_TOKEN_HERE"
	@echo "Reindexing started"

# Production deployment
deploy-prod: ## Deploy to production (GCP Cloud Run)
	@echo "Deploying to production..."
	@echo "This would deploy to GCP Cloud Run"
	@echo "Please configure your GCP credentials first"

# Documentation
docs: ## Generate API documentation
	@echo "Generating API documentation..."
	@echo "Open http://localhost:8000/docs for interactive API docs"
	@echo "Open http://localhost:8000/redoc for ReDoc format"

# Quick start for development
quick-start: ## Quick start for development (minimal stack)
	@echo "Starting minimal development stack..."
	docker-compose -f infra/docker-compose.yml up -d postgres redis
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Starting API in development mode..."
	cd api && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
