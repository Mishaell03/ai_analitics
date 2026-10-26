SHELL := /bin/bash

include .env
export

print-env:
	echo $(POSTGRES_USER)
	echo $(POSTGRES_USER)

DB_URL=jdbc:postgresql://$(DB_HOST):$(DB_PORT)
PSQL_BASE=postgresql://$(POSTGRES_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)

migrate:
	@set -a && source .env && set +a && \
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
	@set -a && source .env && set +a && \
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

.PHONY: s3-refresh

storage-refresh:
	@echo "Refreshing MinIO buckets and seeds..."
	@docker compose run --rm --no-deps minio_init
	@echo "MinIO refresh completed."

fresh:
	@for db in $(shell echo $(DATABASES) | tr ',' ' '); do \
		echo "Reset $$db"; \
		psql $(PSQL_BASE)/$$db \
			-c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
	done
	make migrate
	make seed