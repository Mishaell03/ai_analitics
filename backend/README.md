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
│   │   ├── minio_url.py      # Presigned URL для MinIO
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
│       └── img_convertor.py  # Конвертация изображений
│
├── infra/
│   ├── postgres/
│   │   ├── init/             # SQL инициализация (создание БД)
│   │   └── core_db/
│   │       ├── migrations/   # Flyway миграции (V1__... V5__...)
│   │       └── seeds/        # Тестовые данные (R__*.sql)
│   └── minio/
│       └── seeds/            # Файлы для MinIO (аватары, контент)
│
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
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Запуск сервера

```bash
cd app
python3 main.py
```

Или через uvicorn:

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**API:** http://localhost:8000/api/v1  
**Swagger:** http://localhost:8000/docs

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