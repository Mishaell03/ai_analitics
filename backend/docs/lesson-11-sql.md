# Подготовка урока 11

Контент: `infra/minio/seeds/course-content/1/4/11.md`.
Модуль 4 и урок 11 относятся к курсу 1. Эталоны и ответы находятся только в
`infra/postgres/core_db/seeds/R__lesson_11_answers.sql`, не в Markdown ученика.

## Учебная база

SQL runner подключается к `analytics_training` пользователем `sandbox_reader`.
Миграции и сиды этой БД применяются отдельно от `core_db`; проверьте, что
`analytics_training` включена в `DATABASES` для команд Makefile.

Вместо повторного создания существующей `order_items` применяйте штатные файлы:

- `analytics_training/migrations/V5__severny_svet_order_items.sql` сохраняет
  старую розничную таблицу под именем `retail_order_items` и создаёт новую
  `order_items` для канонического набора «Северный свет».
- `analytics_training/seeds/R__retail_sales.sql` наполняет старый розничный набор.
- `analytics_training/seeds/R__severny_svet.sql` наполняет `order_items` ровно
  десятью каноническими записями при чистом заполнении.

Перед публикацией проверьте владельцем учебной БД:

```sql
SELECT current_database(), to_regclass('public.order_items');
SELECT count(*) FROM public.order_items; -- 10
SELECT count(DISTINCT order_id) FROM public.order_items; -- 8
SELECT count(*), count(DISTINCT order_id), sum(quantity), sum(quantity * unit_price)
FROM public.order_items WHERE status = 'completed'; -- 9, 7, 18, 10650.00
```

Проверьте все девять столбцов, записи и согласованность клиента/даты/статуса
внутри заказа. Затем проверьте реальное подключение `sandbox_reader`, SELECT
и запрет записи. Права новых таблиц зависят от владельца и default privileges;
при необходимости используйте существующий `infra/sandbox/sql-access.sql`
именно в `analytics_training`. Никогда не выполняйте учебные SQL-запросы через
прикладную БД платформы.

Песочница принимает один SELECT за запуск. Поэтому у задания 3 пять отдельных
полей. В задании 1 порядок строк не оценивается; в задании 2 он существенен.

## Изображение

В Markdown подготовлена ссылка `asset:m_72e62512f7eb67e3`.
Файл пока не предоставлен. После добавления файла в
`infra/minio/seeds/course-content/1/media/` нужно проверить его реальный формат,
размер и разрешение, добавить метаданные в `media_files` и связь с уроком 11
в `lesson_media`. До этого изображение не будет отображаться.

## Автопроверки без сервисов

```bash
venv/bin/python -m pytest tests/test_lesson_11_sql.py tests/test_analytics_training_sql.py -q
```

Проверки используют PostgreSQL AST и SQLite для расчётов по каноническим данным.
Они не подтверждают работу PostgreSQL runner, сеть, реальные права или наличие
таблицы в развёрнутой БД — это требует отдельной проверки перед публикацией.
