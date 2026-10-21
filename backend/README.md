# Backend — AI Analytics API

FastAPI приложение для платформы онлайн-обучения.

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
│   │   ├── routes/           # Эндпоинты (auth, courses, users, health)
│   │   ├── services/         # Бизнес-логика
│   │   ├── schemas/          # Pydantic схемы (валидация)
│   │   └── dto/              # Data Transfer Objects
│   ├── models/               # SQLAlchemy модели
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

Бак `lesson-content`:

```
{course_slug}/{module_id}/{lesson_id}.md    # текст урока
{course_slug}/{module_id}/assets/...         # медиафайлы модуля (картинки, видео)
```

В Markdown медиафайлы упоминаются по идентификатору, а не по ссылке:

```markdown
![Схема работы](assets/schema.png)
```

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
    "url": "http://localhost:9000/lesson-content",
    "fields": {
      "key": "ai-development-beginner/1/15.md",
      "Content-Type": "text/markdown",
      "policy": "...",
      "x-amz-signature": "..."
    },
    "file_path": "ai-development-beginner/1/15.md",
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

### Тесты

```bash
python -m pytest
```

---

## Медиафайлы курсов и уроков

Файлы лежат в **приватном** баке `course-media`, в базе хранится
логический идентификатор, физический ключ объекта и метаданные.
Presigned URL в базе не хранится — он выдаётся по запросу и живёт
`MEDIA_URL_TTL` секунд (по умолчанию 600).

### Раскладка в MinIO

```
course-media/
    covers/{course_id}/{file_id}.webp     — обложки курсов
    media/{course_id}/{media_key}.webp    — изображения уроков
    media/{course_id}/{media_key}.mp4     — видео уроков
```

`file_id` и `media_key` — стабильные логические идентификаторы
(`c_…` и `m_…`), они не зависят от пути в MinIO и используются
в ссылках Markdown: `![Описание](asset:m_0123456789abcdef)`.

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
- загруженная обложка автоматически используется в списке курсов и
  в карточке курса вместо старого файла из бака `course-content`.

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
| `MEDIA_BUCKET` | `course-media` | бак с медиа (приватный) |
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
```

--- 