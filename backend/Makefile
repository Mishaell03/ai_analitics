SHELL := /bin/bash

include .env
export

SANDBOX_IMAGE ?= analytics-sandbox:1.0

print-env:
	echo $(POSTGRES_USER)
	echo $(POSTGRES_USER)

DB_URL=jdbc:postgresql://$(DB_HOST):$(DB_PORT)

.PHONY: ai-migrate
ai-migrate:
	@set -e; set -a; source .env; set +a; \
	export FLYWAY_USER="$$POSTGRES_USER" FLYWAY_PASSWORD="$$POSTGRES_PASSWORD"; \
	export FLYWAY_URL="jdbc:postgresql://$${DB_HOST:-127.0.0.1}:$${DB_PORT:-5432}/core_db"; \
	docker run --rm --network host \
		-e FLYWAY_USER -e FLYWAY_PASSWORD -e FLYWAY_URL \
		-v "$(CURDIR)/infra/postgres/core_db/migrations:/flyway/migrations:ro" \
		-v "$(CURDIR)/infra/postgres/core_db/seeds:/flyway/seeds:ro" \
		flyway/flyway -locations=filesystem:/flyway/migrations,filesystem:/flyway/seeds -target=9 migrate

migrate:
	@set -e; set -a && source .env && set +a && \
	for db in $$(echo $$DATABASES | tr ',' ' '); do \
		echo "Migrating $$db"; \
		docker run --rm \
			--network host \
			-v $(PWD)/infra/postgres/$$db/migrations:/flyway/sql \
			flyway/flyway \
			-url=jdbc:postgresql://localhost:5432/$$db \
			-user=$$POSTGRES_USER \
			-password=$$POSTGRES_PASSWORD \
			migrate; \
	done

seed:
	@set -e; set -a && source .env && set +a && \
	for db in $$(echo $$DATABASES | tr ',' ' '); do \
		echo "Seeding $$db"; \
		docker run --rm \
			--network host \
			-v $(PWD)/infra/postgres/$$db/seeds:/flyway/sql \
			flyway/flyway \
			-url=jdbc:postgresql://localhost:5432/$$db \
			-user=$$POSTGRES_USER \
			-password=$$POSTGRES_PASSWORD \
			migrate; \
	done

storage-migrate:
	python -m app.core.minio_migration

.PHONY: sandbox-up sandbox-logs
sandbox-up:
	docker build -t $(SANDBOX_IMAGE) -f infra/sandbox/Dockerfile .
	docker compose -f docker-compose.yaml -f docker-compose.dev.yaml --profile sandbox up -d --build postgres sandbox_runner

sandbox-logs:
	docker compose --profile sandbox logs --tail=100 sandbox_runner

.PHONY: s3-refresh

storage-refresh:
	@echo "Refreshing MinIO buckets and seeds..."
	@docker compose run --rm --no-deps minio_init
	@echo "MinIO refresh completed."

fresh:
	@set -e; set -a && source .env && set +a && \
	for db in $$(echo "$$DATABASES" | tr ',' ' '); do \
		echo "Reset $$db"; \
		PGPASSWORD="$$POSTGRES_PASSWORD" psql \
			-h "$$DB_HOST" -p "$$DB_PORT" -U "$$POSTGRES_USER" -d "$$db" \
			-v ON_ERROR_STOP=1 \
			-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
	done
	$(MAKE) migrate
	$(MAKE) seed
