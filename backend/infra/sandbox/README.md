# Python и SQL Sandbox

## Быстрый запуск

Из `backend/`: `make sandbox-up`. Команда собирает Python-образ и runner,
запускает PostgreSQL и runner с портом `127.0.0.1:8090`.
Нужен доступ текущего пользователя к Docker. Логи: `make sandbox-logs`.
Токен `SANDBOX_RUNNER_TOKEN` (минимум 32 символа) и `SANDBOX_DB_PASSWORD`
задаются в `backend/.env`. Host API теперь читает sandbox-настройки из этого
файла автоматически; переменные окружения имеют приоритет.

Для host runner: `venv/bin/pip install -r app/requirements.txt`, затем
`venv/bin/python -m uvicorn app.services.sandbox.runner:create_app --factory --host 127.0.0.1 --port 8090`.
Не запускайте host runner и Compose runner одновременно на одном порту.

SQL подключается только к `analytics_training` как `sandbox_reader`.
В Compose хост — `postgres`; на хосте `SANDBOX_DB_HOST=127.0.0.1`,
`SANDBOX_DB_PORT=5432`. После пересоздания `public` примените
`infra/sandbox/sql-access.sql` владельцем таблиц именно в `analytics_training`.
Ученик указывает таблицу в SQL, например `SELECT * FROM customers LIMIT 10`.
Результат: `stdout` с JSON `{ "columns": [...], "rows": [...] }` и `success`.
SQL ограничен SELECT, 5 секундами, 1000 строками и 64 KiB вывода.
При недоступном Docker SQL runner продолжает работать; Python возвращает 503.

## Устройство

`POST /api/v1/sandbox/execute` → cookie-аутентификация (`get_current_user`) →
проверка опубликованного курса/модуля/урока, записи на курс и задания →
доверенный профиль → внутренний HTTP runner → новый Docker-контейнер → результат → удаление.

Пример тела запроса (поля `profile`, `memory`, `timeout` запрещены):

```json
{
  "course_slug": "python",
  "module_id": 2,
  "lesson_id": 123,
  "exercise_id": "python-1",
  "code": "import numpy as np\nprint(np.arange(5).sum())"
}
```

Задание должно существовать в Markdown доступного урока; эталон в БД для запуска
не требуется. При запуске ученика runner
получает только его код. Эталон выполняется отдельно при сохранении урока.
Runner выполняет код; API сравнивает вывод с сохранённым результатом эталона
и возвращает `is_correct`. Прохождение засчитывается только при `is_correct=true`.
Сохраняется существующий формат ошибок `{"detail": {"code": "...", "message": "..."}}`.
Для запросов из браузера действуют существующие cookie/CSRF/CORS-правила платформы.

Пример результата:

```json
{
  "stdout": "10\n",
  "stderr": "",
  "exit_code": 0,
  "timed_out": false,
  "duration": 0.254,
  "output_limited": false,
  "memory_limited": false,
  "success": true
}
```

`duration` — секунды от начала создания контейнера до получения его состояния,
без финального удаления. Ошибки Python — обычный результат с ненулевым `exit_code`.
Перегрузка — HTTP 503 `SANDBOX_BUSY` с `Retry-After: 1`; недоступность Docker/runner —
503 `SANDBOX_UNAVAILABLE`, без внутренних подробностей. Очереди нет: лишний запрос
отклоняется сразу, frontend может повторить его позже.

## Разделение полномочий

- `sandbox_api` не содержит Docker CLI, не монтирует сокет/каталоги хоста и работает
  под uid 65534. Это рекомендуемый способ запуска API для проверки разделения прав.
- Только доверенный `sandbox_runner` получает Docker socket. Это административный
  доступ к Docker-хосту; runner нельзя публиковать в Интернет или подключать к сетям БД/MinIO.
- Между API и runner — отдельная `internal`-сеть и случайный Bearer-токен.
  В dev наружу опубликован только `127.0.0.1:8090`; основной Compose порт не публикует.
- В runner передаются только его настройки, без `env_file` с секретами приложения.
  В student-контейнер не передаются ни токен runner, ни окружение API/runner.
- Один экземпляр runner, один worker, общий persistent lock-volume. Счётчики
  находятся в этом отдельном процессе, а не в FastAPI приложения. Блокировка не
  даёт запустить второго владельца с тем же volume. **Не масштабировать runner,
  не запускать параллельно host-runner с другим lock-файлом на том же Docker daemon.**

Профили централизованы в `app/services/sandbox/config.py`:

| Профиль | CPU | RAM (swap запрещён) | Время |
|---|---:|---:|---:|
| light | 0.25 | 256m | 5 с |
| standard | 0.5 | 768m | 15 с |
| heavy | 1 | 1536m | 30 с |

Одновременно максимум 3 выполнения, из них максимум 1 heavy. При ошибке удаления
новые задания блокируются до успешной очистки watchdog. Контейнеры имеют managed-label
и deadline; watchdog удаляет просроченные каждую секунду, при запуске runner удаляет
оставшиеся managed-контейнеры предыдущего процесса. Не используйте этот label для
других сервисов.

## Изоляция выполнения

Каждый запуск: `--network none`, read-only root, uid/gid 65534, `cap-drop ALL`,
`no-new-privileges`, private IPC/cgroup namespace, стандартный Docker seccomp,
CPU/RAM/pids limits, 64 процесса, `/tmp` tmpfs 64m с noexec/nosuid/nodev,
`/dev/shm` 8m, лимиты файловых дескрипторов/размера файла/core dump.
Нет bind mounts, Docker socket, host PID/IPC/network или privileged-режима.
Логи Docker отключены; stdout+stderr суммарно ограничены 64 KiB, превышение
останавливает выполнение. Код ограничен 64 KiB UTF-8, JSON-тело — отдельным
лимитом до разбора. Образ не скачивается автоматически (`--pull=never`).

Matplotlib работает с `MPLBACKEND=Agg`, временные файлы можно писать в `/tmp`.
Графики пока не возвращаются клиенту как изображения. Не устанавливаются пакеты
из кода ученика: сети нет, root filesystem read-only.

Внешний таймер runner принудительно останавливает контейнер, независимо от кода
ученика. `timeout` внутри образа — только дополнительный предохранитель.
Удаление выполняется и при отмене запроса; watchdog повторяет неудавшееся удаление.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `SANDBOX_IMAGE` | `analytics-sandbox:1.0` | Доверенный образ; должен быть собран заранее |
| `SANDBOX_RUNTIME` | `runc` | На production можно задать `runsc` после отдельной настройки |
| `SANDBOX_RUNNER_TOKEN` | пусто | Обязательный случайный секрет, минимум 32 символа, одинаковый у API/runner |
| `SANDBOX_RUNNER_ENDPOINT` | `http://127.0.0.1:8090` | Адрес для API; Compose API использует `http://sandbox_runner:8090` |
| `SANDBOX_CONCURRENCY` | `3` | Можно уменьшить до 1–2, увеличить выше 3 нельзя |
| `SANDBOX_HEAVY_CONCURRENCY` | `1` | Увеличение запрещено |
| `SANDBOX_ASSIGNMENT_PROFILES` | `{}` | JSON переопределений `"lesson_id:exercise_id": "profile"`, по умолчанию `light`, только в окружении API |
| `SANDBOX_LOCK_FILE` | `.sandbox-runner.lock` | При host-запуске; в Compose задан путь в общем runner-volume |
| `SANDBOX_DOCKER_SOCKET` | `/var/run/docker.sock` | Исходный путь socket для Compose; можно указать Docker Desktop/rootless socket |

Для доступного Python-задания без переопределения используется `light`. Изменение
профиля — административное изменение конфигурации, не поле запроса ученика.
Секреты не хранить в образе и не коммитить. Docker build context исключает `.env`.

## Запуск на macOS ARM64 / Fedora

Все команды из `backend/`. Нужны работающий Docker и уже собранный sandbox-образ.
Устанавливать gVisor или пересобирать student-образ для запуска не требуется.

1. В `backend/.env` задайте `SANDBOX_RUNNER_TOKEN` и при необходимости профили заданий,
   например `SANDBOX_ASSIGNMENT_PROFILES={"123:python-1":"standard"}`.
   Секрет можно сгенерировать существующим Python:

   ```bash
   venv/bin/python -c 'import secrets; print(secrets.token_hex(32))'
   ```

2. Убедитесь, что переменные БД/MinIO для контейнерного API находятся в
   `backend/.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `MINIO_ACCESS_KEY`,
   `MINIO_SECRET_KEY` и остальные настройки приложения). В проекте host-API
   читает `app/.env`, но **этот файл не копируется в образ**. Compose переопределяет
   DB_HOST/MINIO_ENDPOINT именами сервисов. На production отдельно настройте
   `IS_PRODUCT`, `CORS_ORIGINS` и cookie-параметры.

3. Запустите только добавленные сервисы (существующие PostgreSQL/MinIO должны
   уже работать; миграции эта команда не запускает):

   ```bash
   docker compose -f docker-compose.yaml -f docker-compose.dev.yaml --profile sandbox --profile sandbox-api up -d --build --no-deps sandbox_runner sandbox_api
   ```

   API: `http://127.0.0.1:8000/api/v1`, Swagger: `http://127.0.0.1:8000/docs`.
   Авторизуйтесь существующим способом и отправьте пример запроса выше.
   Не запускайте одновременно host-API на порту 8000.

Host-API может использовать внутренний endpoint для отладки, но процесс на macOS
под пользователем с доступом к Docker **не удовлетворяет разделению полномочий**.
Для него sandbox-переменные задаются в окружении/`app/.env`. Для безопасной проверки
используйте контейнерный API, не выдавайте ему socket и права Docker.
На Fedora при SELinux не отключайте SELinux и не перемаркировывайте системный
Docker socket через `:Z` ради запуска: настройте политику отдельно при необходимости.

## Тестирование

Unit/regression (без БД, без сетевых запросов к сервисам):

```bash
venv/bin/python -m pytest tests/test_sandbox.py tests/test_request_body_middleware.py tests/test_exercise_check.py tests/test_csrf.py -q
```

Docker integration запускает только готовый student-образ, не выполняет миграции,
не требует PostgreSQL/MinIO. **Остановите runner и дождитесь завершения заданий
перед тестами**: тест восстановления проверяет удаление managed-контейнеров.
Тесты не должны выполняться параллельно с реальной нагрузкой или через pytest-xdist.

```bash
docker compose --profile sandbox stop sandbox_runner
SANDBOX_DOCKER_TESTS=1 venv/bin/python -m pytest tests/test_sandbox_docker.py -q
docker ps -a --filter label=analytics.sandbox=1
```

Дополнительно можно проверить собранный runner как реальный отдельный контейнер
(временный тестовый runner удаляется; приложение и БД не запускаются):

```bash
docker compose --profile sandbox build sandbox_runner
SANDBOX_DOCKER_TESTS=1 SANDBOX_RUNNER_TEST_IMAGE=backend-sandbox_runner venv/bin/python -m pytest tests/test_sandbox_docker.py -q
```

Имя runner-образа зависит от Compose project name; при своём project name замените
`backend-sandbox_runner` соответствующим именем образа.

Покрытие: Python/NumPy/pandas/Agg, syntax errors, бесконечный цикл, RAM/OOM,
таймаут, чрезмерный и невалидный UTF-8 вывод, недоверенные профили, лимиты
конкурентности, HTTP-аутентификация runner, single-owner lock, отмена запроса,
восстановление после сбоя, реальные настройки изоляции и отсутствие контейнеров
после выполнения. Docker-тесты без явного opt-in пропускаются.

### Фактическая проверка на macOS ARM64 (26.10.2026)

- Unit/regression-команда выше: **56 passed**. Одно существующее предупреждение
  Starlette о deprecated httpx TestClient; зависимости ради него не менялись.
- Docker-команда с `SANDBOX_RUNNER_TEST_IMAGE`: **16 passed**, включая отдельный
  контейнер runner, настоящий HTTP внутри него и запуск NumPy в student-контейнере.
- `docker compose ... config --quiet`: успешно. Отдельно проверена передача JSON
  allowlist через Compose без повреждения значения.
- `docker compose --profile sandbox build sandbox_runner`: успешно; Debian
  `docker-cli` установлен без ненужного Docker daemon.
- После тестов managed student-контейнеров и временного test-runner не осталось.
- Контейнерный API не запускался; отсутствие его Docker-доступа проверено по
  Compose/Dockerfile, а доступ к заданиям — unit-тестами. Настоящие сессии/БД,
  Fedora, Debian AMD64 и `runsc` в этой проверке не использовались.

## Перед production Debian AMD64

Это проверенный development-путь, **не утверждение о production-safe изоляции**.

- Собрать/проверить образы для AMD64, зафиксировать версии Python-пакетов и
  digest образов, настроить сканирование и обновление образов/ядра/Docker.
- На выделенном sandbox-хосте установить и настроить gVisor отдельно, задать
  `SANDBOX_RUNTIME=runsc`, повторить security/resource/integration-тесты.
  На `runc` недоверенный код разделяет ядро Docker-хоста: контейнер не заменяет VM.
- Проверить cgroups v2, swap/OOM, pids/tmpfs/seccomp и доступный бюджет RAM/CPU
  под реальной нагрузкой. Резервировать ресурсы также для Docker и runner.
- Сокет даёт runner административные возможности: не размещать на этом daemon
  БД, MinIO и другие чувствительные сервисы. Не публиковать runner; между хостами
  использовать защищённую приватную сеть и mTLS/аналогичную защиту транспорта.
- Обеспечить restart/мониторинг runner, внешний reaper managed-контейнеров и
  оповещение о сбоях cleanup. При полном падении runner/daemon мгновенное удаление
  невозможно; внутриконтейнерный таймер не является неподконтрольным ученику.
  При рестарте текущий runner удаляет остатки, но не обещает очистку при навсегда
  остановленном сервисе. До production эту аварийную ситуацию нужно проверить.
- Сохранить единственного владельца общего lock-volume. Для нескольких хостов
  потребуется отдельный глобальный планировщик — текущая реализация не кластерная.
- Настроить TLS внешнего API, ротацию секрета, reverse-proxy body/time/rate limits,
  пользовательские квоты/защиту от постоянного занятия всех трёх слотов и мониторинг.
- Отдельно проверить endpoint с настоящей пользовательской сессией и существующим
  заданием в staging. Unit-тесты доступа используют моки, БД в этой задаче не изменяется.
