# Backend — AI Analytics API

FastAPI приложение для платформы онлайн-обучения.

Python Sandbox: [архитектура, запуск, настройки и тесты](infra/sandbox/README.md).
AI-наставник: [DeepSeek API, отдельная память каждого урока и боковой чат](docs/lesson-ai.md).

---

## Структура

```
backend/
├── app/
│   ├── main.py               # Точка входа FastAPI
│   ├── Dockerfile            # Сборка образа Backend
│   ├── core/                 # Инфраструктный слой
│   │   ├── config.py         # Настройки из .env
│   │   ├── database.py       # SQLAlchemy async engine + сессии
│   │   ├── session.py        # Проверка текущего пользователя
│   │   ├── users_events_logs.py  # Логирование событий
│   │   ├── pagination.py     # Пагинация
│   │   ├── minio_url.py      # Работа с MinIO (URL, upload, чтение файлов)
│   │   ├── storage_paths.py  # Раскладка файлов в MinIO (пути уроков и медиа)
│   │   ├── markdown/         # Разбор и очистка Markdown урока
│   │   ├── clients_ip.py     # Определение IP клиента
│   │   └── errors.py         # Обработка ошибок
│   ├── api/v1/               # API слой
│   │   ├── router.py         # Общий роутер /api/v1
│   │   ├── routes/           # Эндпоинты (auth, courses, users, exercises)
│   │   ├── services/         # Бизнес-логика
│   │   ├── schemas/          # Pydantic схемы (валидация)
│   │   └── dto/              # Data Transfer Objects
│   ├── models/               # SQLAlchemy модели (courses, media, exercises)
│   └── utils/                # Утилиты
│       ├── img_convertor.py  # Проверка и конвертация изображений
│       ├── video_inspector.py  # Проверка MP4 и кодеков
│       └── phone.py          # Нормализация телефона
│
├── infra/
│   ├── postgres/
│   │   ├── init/             # SQL инициализация (создание БД)
│   │   └── core_db/
│   │       ├── migrations/   # Flyway миграции (V1__... V7__...)
│   │       └── seeds/        # Тестовые данные (R__*.sql)
│   └── minio/
│       └── seeds/            # Файлы для MinIO (аватары, контент)
│
├── tests/                    # Юнит-тесты (pytest)
├── docker-compose.yaml       # Docker compose конфиг
├── Makefile                  # Flyway DB миграции и сиды для PostgreSQL
└── requirements.txt          # Python зависимости             
```

---

## Запуск

### 1. Окружение

Создайте `.env` в текущей директории и поменяйте на свои значения:

```bash
cp .env.example .env
```

### 2. Инфраструктура (Docker)

```bash
docker-compose up -d
```

Поднимает:
- **PostgreSQL** — порт `5432`
- **MinIO** — порт `9000` (API), `9001` (консоль)
- **pgAdmin** — порт `5050` (только с профилем `dev`: `docker-compose --profile dev up -d`)

### 3. Миграции и сиды

При первой инициализации PostgreSQL скрипты из `infra/postgres/init` создают
`core_db`, отдельную пустую БД `analytics_training` и пользователя `sandbox_reader`.
Задайте непустой `SANDBOX_DB_PASSWORD` в `.env` до запуска Compose.
В `analytics_training` пользователь может читать учебные таблицы в схеме `public`,
но не изменять данные, создавать таблицы или временные объекты.
Схема `public` предназначена только для одобренных учебных таблиц:
скрипт разрешает чтение всех таблиц этой схемы.
Чтение будущих таблиц автоматически разрешается, если их создаёт администратор,
выполнивший init-скрипт (`POSTGRES_USER`). Для таблиц других владельцев нужны
отдельные `GRANT SELECT` / `ALTER DEFAULT PRIVILEGES FOR ROLE ...`.

**Полная изоляция от прикладных БД не гарантируется.** Скрипт не меняет их ACL,
а выводит аудит `CONNECT`: права `PUBLIC`, эффективные права пользователя
(включая наследование) и возможность подключения через `SET ROLE`.
`REVOKE ... FROM sandbox_reader` не отменяет разрешения от `PUBLIC`.
Проверка отражает права PostgreSQL; правила аутентификации `pg_hba.conf`
могут дополнительно ограничивать фактическое подключение.
Если у существующего `sandbox_reader` есть членство в ролях или он владеет БД
либо учебными объектами, скрипт останавливается для ручной проверки, не удаляя
членство и не меняя владельцев. Прочие роли и миграции не изменяются.
Эффективные права записи на таблицы, столбцы и последовательности проверяются
во всех схемах учебной БД, как и права создания объектов. Ошибка указывает
конкретный объект с избыточными правами. Владение проверяется также для функций,
типов и других объектов через системный каталог зависимостей владельцев.
Неожиданное чтение вне `public` и доступный `EXECUTE` для пользовательских функций,
`SECURITY DEFINER` и ряда потенциально опасных встроенных функций выводятся как
предупреждения с именами объектов. Тела функций не выполняются и не выводятся.
Это аудит, а не доказательство безопасности функций: расширения, представления,
RLS-политики и вызываемые ими функции требуют ручной проверки. Предупреждения
нельзя игнорировать перед включением выполнения недоверенного SQL.

Только для пары `sandbox_reader` / `analytics_training` устанавливаются
`default_transaction_read_only=on`, `statement_timeout=5s`,
`transaction_timeout=10s`, `lock_timeout=2s` и
`idle_in_transaction_session_timeout=10s`. В PostgreSQL 18 при равенстве
`transaction_timeout` и idle-таймаута последний игнорируется: время всей
транзакции ограничено 10 секундами. Lock-таймаут меньше statement-таймаута,
поэтому ожидание блокировки прерывается раньше выполнения запроса.
Это начальные параметры сессии,
а не непреодолимые ограничения: SQL-пользователь может изменить их через `SET`.
Штатный `PUBLIC UPDATE` на `pg_catalog.pg_settings` также позволяет менять
настройки сессии; аудит выводит предупреждение об этом, не отзывает системный
грант и не считает его ошибкой свежей установки PostgreSQL.
На уровне роли дополнительно задаётся `CONNECTION LIMIT 5`: он действует на
обычные подключения `sandbox_reader` во всех БД, а не только в учебной.
Это не ограничение числа запросов на пользователя платформы и не замена пулу
соединений/очереди; PostgreSQL проверяет лимит приблизительно при конкуренции.
Защита от записи обеспечивается также ACL.
Для недоверенного произвольного SQL используйте отдельный экземпляр PostgreSQL
без прикладных данных, с внешними лимитами времени/ресурсов и контролем запросов.

Init-скрипты **не запускаются повторно** на существующем томе PostgreSQL.
Чтобы применить настройку без удаления данных, после задания пароля выполните:

```bash
# Обновить окружение контейнера PostgreSQL из .env.
docker compose up -d postgres
docker compose exec -T postgres sh -c 'psql -X -U "$POSTGRES_USER" -d postgres -f /docker-entrypoint-initdb.d/001_create_sandbox_user.sql'
```

Скрипт можно запускать повторно: он сохраняет БД и данные, обновляет пароль,
учебные права и параметры новых сессий. Не используйте `psql --single-transaction`:
`CREATE DATABASE` нельзя выполнять внутри транзакции. При ошибке уже выполненные
команды могут сохраниться; после устранения причины повторите запуск.
Если старая версия скрипта уже отозвала `PUBLIC CONNECT` у прикладных БД,
новая версия не восстанавливает его автоматически: сначала проверьте прежние
ACL/резервные копии и восстановите только подтверждённые разрешения вручную.
Подключение для чтения: хост `postgres` из контейнеров (или `127.0.0.1:5432`
с `docker-compose.dev.yaml`), БД `analytics_training`, логин `sandbox_reader`,
пароль из `SANDBOX_DB_PASSWORD`. Не добавляйте эту пустую БД в `DATABASES`,
пока для неё нет отдельных Flyway-миграций.

#### SQL Runner

`app/services/sandbox/sql_runner.py` выполняет один SELECT к таблицам `public`
в `analytics_training` через отдельное подключение `sandbox_reader`, READ ONLY.
Таблицы указывает сам ученик. Используются PostgreSQL AST, набор разрешённых
функций, лимит времени 5 секунд и потоковое чтение до 1000 строк / 64 KiB.
Основной SQLAlchemy engine для SQL учеников не используется.

Запуск Python и SQL: `make sandbox-up`. Настройки берутся из `backend/.env`;
переменные окружения имеют приоритет. Подробнее: [Sandbox](infra/sandbox/README.md).
После пересоздания схемы `public` восстановите права чтения скриптом
`infra/sandbox/sql-access.sql`, подключившись владельцем таблиц к `analytics_training`.

Проверки на отдельном одноразовом PostgreSQL 18.6 (без продуктовых томов,
портов и подключений; нужен локальный образ и Docker):

```bash
POSTGRES_SANDBOX_TESTS=1 python -m pytest tests/test_postgres_sandbox.py -q
```

```bash
# Применить миграции
make migrate

# Загрузить тестовые данные
make seed

# Сбросить БД и применить заново
make fresh
```

### 4. Python зависимости

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Запуск сервера
в корне backend сервиса
```bash
python -m app.main
```


**API:** http://localhost:8000/api/v1  
**Swagger:** http://localhost:8000/docs

---

## Уроки: БД + MinIO

Метаданные урока (название, описание, позиция, связи с модулем и курсом)
лежат в БД, а сам текст урока — отдельным Markdown-файлом в MinIO.

### Раскладка в MinIO

Все файлы курса лежат в баке `course-content`, внутри каталога курса:

```
{course_id}/main.webp                     # обложка курса
{course_id}/content.md                    # вводный текст курса
{course_id}/{module_id}/content.md        # вводный текст модуля
{course_id}/{module_id}/{lesson_id}.md    # текст урока
{course_id}/media/{media_key}.webp|.mp4   # медиафайлы урока
```

В Markdown медиафайлы упоминаются по идентификатору, а не по ссылке:

```markdown
![Схема работы](asset:m_0123456789abcdef)
```

Старые объекты из `course-media`, `lesson-content` и `module-content`
переносятся в `course-content` автоматически при старте приложения
(`MINIO_MIGRATE_ON_STARTUP=true`). Перенос идемпотентен: объект сначала
копируется и проверяется, и только потом удаляется старый.

### Получение урока

```
GET /api/v1/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/content
```

Backend проверяет, что курс, модуль и урок опубликованы, проверяет, что
пользователь записан на курс (администраторам доступно всегда), читает
Markdown из MinIO, очищает его и отдаёт клиенту:

```json
{
  "lesson": {"lesson_id": 1, "title": "...", "position": 1, "content_url": "..."},
  "content": "# Заголовок\n\nТекст урока",
  "content_type": "markdown",
  "custom_blocks": [{"type": "test", "content": "...", "implemented": false}],
  "assets": [{"asset_id": "schema.png", "kind": "image", "alt": "Схема", "url": null}]
}
```

- `content` — очищенный Markdown: сырой HTML и опасные протоколы ссылок
  (`javascript:`, `data:`) удаляются, содержимое блоков кода не трогается;
- `custom_blocks` — кастомные блоки урока (`:::тип ... :::`). Логика блоков
  (тесты, видео, задания с кодом) появится позже, поэтому у них
  `implemented: false`;
- `assets` — медиафайлы, упомянутые в уроке. `url` заполнится на этапе
  выдачи медиафайлов (presigned URL).

### Уроки в админке

Администратору доступны черновики, поэтому у него свои маршруты:

```
GET   /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons
GET   /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/content
PATCH /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}
```

- список уроков отдаёт и неопубликованные уроки, а в поле `has_content`
  показывает, есть ли Markdown урока в MinIO;
- содержимое урока очищается теми же правилами, что и для пользователя:
  админ видит ровно то, что увидит ученик после публикации;
- `PATCH .../lessons/{lesson_id}` меняет метаданные урока (название,
  описание, позиция, публикация): текст урока лежит в хранилище,
  поэтому он меняется через загрузку.

Оба маршрута закрыты `get_current_admin`: обычному пользователю
возвращается 403.

### Создание урока и загрузка Markdown

Урок создаётся в два шага: сначала запись в БД, затем загрузка файла
в MinIO по ссылке, которую выдаёт backend.

```
POST /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons
POST /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/upload-url
```

Ответ на создание (и на запрос новой ссылки) содержит адрес и поля формы
для прямой загрузки файла в MinIO:

```json
{
  "lesson_id": 15,
  "title": "Урок",
  "position": 3,
  "is_published": false,
  "has_content": false,
  "upload": {
    "url": "http://localhost:9000/course-content",
    "fields": {
      "key": "1/1/15.md",
      "Content-Type": "text/markdown",
      "policy": "...",
      "x-amz-signature": "..."
    },
    "file_path": "1/1/15.md",
    "max_size": 512000,
    "expires_in": 900
  }
}
```

Клиент отправляет все поля формы вместе с файлом:

```js
const form = new FormData();

Object.entries(upload.fields).forEach(([name, value]) => form.append(name, value));
form.append("file", new Blob([file], { type: "text/markdown" }), file.name);

await fetch(upload.url, { method: "POST", body: form });
```

- размер файла ограничен 500 КБ (`LESSON_CONTENT_MAX_UPLOAD_SIZE`);
  проверяет это сам MinIO — при превышении загрузка отклоняется
  с ошибкой `EntityTooLarge`;
- ключ объекта зафиксирован политикой: файл можно записать только
  по пути урока;
- ссылка живёт `UPLOAD_URL_TTL` секунд (по умолчанию 900), поэтому для
  перезаписи файла её можно запросить заново;
- если ссылка не построилась, урок не сохраняется в БД.

### Удаление урока

```
DELETE /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}
DELETE /api/v1/admin/lessons/{lesson_id}
```

Удаляются и запись в БД, и Markdown-файл урока в MinIO.

- запись в БД удаляется первой: если файл в хранилище почему-то не
  удалится, останется лишний файл, а не урок без текста;
- позиции оставшихся уроков модуля пересобираются в `1..N`, чтобы
  после удаления не было пропусков;
- попытки урока (`lesson_attempts`) удаляются каскадом на уровне БД.

### Перестановка модулей и уроков

```
PUT /api/v1/admin/courses/{course_slug}/modules/reorder
PUT /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/reorder
PUT /api/v1/admin/modules/{module_id}/lessons/reorder
```

Клиент присылает id в новом порядке, backend переназначает `position = 1..N`
одной транзакцией и возвращает список в новом порядке:

```json
{ "module_ids": [4, 3] }
```

```json
{ "lesson_ids": [2, 1] }
```

- список должен содержать **все** модули курса (или все уроки модуля),
  иначе `UPDATE_ME_FAILED`;
- позиции ставятся в два шага (сначала временные, потом финальные) —
  иначе уникальный индекс `(курс/модуль, позиция)` ругается на
  промежуточное состояние при перестановке;
- ответ содержит актуальные позиции и `has_content` у уроков.

### Правильные ответы на задания

Задания (тесты) хранятся в Markdown урока, правильные ответы — в БД.
Связь идёт через `exercise_id`: он указан в Markdown задания и
повторяется в ключе записи, поэтому ответ переживает правку текста.

Разметка задания в Markdown:

```
:::test
id: python-variables
Текст задания
:::
```

Идентификатор задаётся первой строкой содержимого блока. В ответе с
содержимым урока он приходит в `custom_blocks[].data.exercise_id`.

```
POST   /api/v1/admin/lessons/{lesson_id}/exercises/{exercise_id}/answer
DELETE /api/v1/admin/lessons/{lesson_id}/exercises/{exercise_id}/answer
GET    /api/v1/admin/lessons/{lesson_id}/exercises
```

- `POST` создаёт ответ или обновляет существующий — это один эндпоинт;
- `DELETE` убирает ответ задания;
- `GET` отдаёт все ответы урока (у урока без заданий список пустой);
- `exercise_id` — буквы, цифры, дефис и подчёркивание, до 64 символов;
- правильный ответ не пустой, до 10000 символов;
- создавать, изменять и удалять ответы может только админ.

Ключ `reference` зарезервирован под **эталонный ответ урока** — пример
идеального решения задачи, который не привязан ни к одному заданию.
Админка сохраняет его тем же эндпоинтом, но с этим ключом вместо
`exercise_id`: код в базу уходит как есть, а код ученика с эталоном
автоматически не сравнивается.

### Тесты

```bash
python -m pytest
```

---

## Медиафайлы курсов и уроков

Все файлы лежат в **приватном** баке `course-content`, в базе хранится
логический идентификатор, физический ключ объекта и метаданные.
Presigned URL в базе не хранится — он выдаётся по запросу и живёт
`MEDIA_URL_TTL` секунд (по умолчанию 600).

### Раскладка в MinIO

```
course-content/
    {course_id}/main.webp                       — обложка курса
    {course_id}/media/{media_key}.webp          — изображения уроков
    {course_id}/media/{media_key}.mp4           — видео уроков
```

`file_id` и `media_key` — стабильные логические идентификаторы
(`c_…` и `m_…`). `media_key` не зависит от пути в MinIO и используется
в ссылках Markdown: `![Описание](asset:m_0123456789abcdef)`. Обложка
всегда лежит по фиксированному пути `{course_id}/main.webp`.

### Обложка курса

```
POST   /api/v1/admin/courses/{course_slug}/image   — загрузить или заменить
GET    /api/v1/admin/courses/{course_slug}/image   — метаданные (админ)
DELETE /api/v1/admin/courses/{course_slug}/image   — удалить
GET    /api/v1/courses/{course_slug}/image         — метаданные со ссылкой
```

- файл проверяется по содержимому (не по расширению), пережимается
  в WebP с сохранением пропорций, метаданные (EXIF, GPS) не сохраняются;
- замена безопасна: новый файл сначала уходит в хранилище, потом
  меняется запись в БД, и только после этого удаляется старый файл —
  при сбое у курса остаётся рабочая обложка;
- обложка автоматически используется в списке курсов и в карточке
  курса по пути `{course_id}/main.webp`.

### Медиафайлы урока

```
POST   /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media
GET    /api/v1/admin/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media
GET    /api/v1/admin/media/{media_key}
POST   /api/v1/admin/media/{media_key}/url
DELETE /api/v1/admin/media/{media_key}
POST   /api/v1/admin/lessons/{lesson_id}/media/{media_key}      — привязать к уроку
DELETE /api/v1/admin/lessons/{lesson_id}/media/{media_key}      — отвязать от урока
GET    /api/v1/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media
GET    /api/v1/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media/{media_key}/url
```

- **изображения** конвертируются в WebP, метаданные удаляются;
- **видео** сохраняется как есть, но проверяется реальный контейнер
  и кодеки: нужен MP4 с H.264 и AAC — такой файл играет во всех
  браузерах без перекодирования;
- видео **не читается в память целиком**: контейнер разбирается
  по структуре боксов, файл уходит в MinIO потоком (MinIO сам
  разобьёт файл на части, если он больше 5 ГБ — лимит у нас 200 МБ);
- один файл можно использовать в нескольких уроках курса: при
  удалении из одного урока файл остаётся, пока на него есть ссылки;
- ссылку на файл получают только записанные на курс пользователи
  (администраторы — всегда); ссылка короткоживущая, новую можно
  запросить снова.

### Ограничения (в `.env`)

| Переменная | По умолчанию | Значение |
|---|---|---|
| `MINIO_MIGRATE_ON_STARTUP` | `true` | переносить старые файлы в `course-content` при старте |
| `MEDIA_URL_TTL` | `600` | срок жизни ссылки, секунды |
| `MEDIA_MAX_IMAGE_SIZE` | `10485760` | максимальный размер изображения, байт |
| `MEDIA_MAX_VIDEO_SIZE` | `209715200` | максимальный размер видео, байт |
| `MEDIA_MAX_IMAGE_DIMENSION` | `6000` | максимальная сторона изображения, пиксели |
| `MEDIA_MAX_VIDEO_DIMENSION` | `4096` | максимальная сторона видео, пиксели |
| `MEDIA_MAX_IMAGE_PIXELS` | `40000000` | максимум пикселей изображения (защита от bomb-файлов) |
| `MEDIA_IMAGE_QUALITY` | `82` | качество WebP |
| `MEDIA_ALLOWED_IMAGE_TYPES` | `image/jpeg,image/png,…` | допустимые MIME-типы изображений |
| `MEDIA_ALLOWED_VIDEO_TYPES` | `video/mp4` | допустимые MIME-типы видео |

---

## Команды

```bash
# Docker
docker-compose up -d          # запуск
docker-compose down           # остановка
docker-compose down -v        # остановка + удалить данные
docker-compose logs -f        # логи

# Миграции
make migrate                  # применить миграции
make seed                     # загрузить сиды
make fresh                    # сбросить БД + миграции + сиды
make storage-migrate          # перенести старые файлы MinIO в course-content
make storage-refresh          # обновить файлы MinIO
```

---
