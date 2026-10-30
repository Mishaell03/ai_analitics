#!/bin/sh
# Полная очистка бакетов проекта и повторная загрузка seeds.
# Запускается в сети уже работающего MinIO, без управления сетями Compose.
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
seeds_dir=${MINIO_SEEDS_DIR:-/seeds}

# Проверяем источники до первого удаления, а не после очистки бакетов.
for bucket in default-avatars course-content; do
    if [ ! -d "$seeds_dir/$bucket" ]; then
        echo "Missing seed directory: $seeds_dir/$bucket" >&2
        exit 1
    fi
done

mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

# Не трогаем чужие бакеты. Удаляем и старые версии объектов, если они есть.
for bucket in default-avatars avatars course-content; do
    mc mb --ignore-existing "local/$bucket"
    mc rm --recursive --force --versions "local/$bucket"
done

mc cp --recursive "$seeds_dir/default-avatars/" local/default-avatars
mc cp --recursive "$seeds_dir/course-content/" local/course-content
