.PHONY: help build up down restart logs ps clean backup

# Default target
help:
	@echo "Agent ADK Data Search - Make Commands"
	@echo "======================================"
	@echo "make build        - Build Docker images"
	@echo "make up           - Start all services"
	@echo "make down         - Stop all services"
	@echo "make restart      - Restart all services"
	@echo "make logs         - View logs (all services)"
	@echo "make logs-app     - View application logs"
	@echo "make logs-db      - View database logs"
	@echo "make ps           - Show running containers"
	@echo "make clean        - Remove containers and images"
	@echo "make backup       - Backup database and ChromaDB"
	@echo "make shell-app    - Open shell in app container"
	@echo "make shell-db     - Open PostgreSQL shell"

# Build images
build:
	docker-compose build

# Start services
up:
	docker-compose --env-file .env.production up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

logs-db:
	docker-compose logs -f postgres

logs-chroma:
	docker-compose logs -f chromadb

# Show container status
ps:
	docker-compose ps

# Clean up
clean:
	docker-compose down -v --rmi all

clean-volumes:
	docker-compose down -v

# Backup
backup:
	@echo "Backing up PostgreSQL..."
	@mkdir -p backups
	@docker exec agent-adk-postgres pg_dump -U postgres agent_production_db > backups/postgres_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backing up ChromaDB..."
	@docker run --rm -v agent-adk-data-search_chromadb_data:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/chromadb_backup_$$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "Backup completed! Check ./backups/ directory"

# Shell access
shell-app:
	docker exec -it agent-adk-app /bin/bash

shell-db:
	docker exec -it agent-adk-postgres psql -U postgres -d agent_production_db

# Development
dev:
	docker-compose --env-file .env up

dev-build:
	docker-compose --env-file .env up --build

# Health check
health:
	@echo "Checking services health..."
	@docker-compose ps
	@echo "\nChecking PostgreSQL..."
	@docker exec agent-adk-postgres pg_isready -U postgres || echo "PostgreSQL is not ready"
	@echo "\nChecking ChromaDB..."
	@curl -s http://localhost:8000/api/v1/heartbeat || echo "ChromaDB is not ready"

# Update and restart
update:
	git pull origin main
	docker-compose build
	docker-compose up -d

# Install dependencies locally
install:
	pip install -r requirements.txt
