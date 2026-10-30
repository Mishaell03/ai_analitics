# Урок 12: аудит и ручная публикация

**Статус: НЕ ГОТОВ к публикации.** Исходные три обязательных редактора пока
содержат `id: none`; публиковать такой файл нельзя: `none` намеренно означает
необязательную свободную практику, а не связь с эталоном.

## Источники и обнаруженные блокеры

Из `/home/adminss/Загрузки/lesson_12_REDOWNLOAD/` прочитаны
`lesson_12_teacher.md`, `lesson_12_answer_key.txt`, `lesson_12_admin_checklist.md`.
**`lesson_12_student.md` в этой папке отсутствует.** Для локальной сверки использован
уже существующий `infra/minio/seeds/course-content/1/4/12.md` (380 строк до правок).
Оригинальные файлы преподавателя не изменялись.

В `core_db/seeds/R__courses.sql` числовой `lesson_id=12` относится к курсу 3,
модулю 6, уроку «Мониторинг и оптимизация AI-систем». Это **не** SQL-урок 12.
Для SQL-урока нужен фактический ID записи начального курса, модуль с позицией 4,
урок с позицией 2. Нельзя переименовывать/перемещать существующий урок другого курса.

Read-only аудит доступной БД не подтвердил три записи эталонов или metadata
`m_45e57512f7eb46e0`. Во время первого чтения запись ID 12 относилась к другому
курсу; при последующем чтении каталог курсов был пуст. Обе проверки выполнялись
без записи. Поэтому миграции/seed-команды здесь не запускались и ни один ID
не объявлен существующим. Требуется стабильная целевая БД владельца.

При первом аудите в доступной `analytics_training` схема retail присутствовала,
но `retail_order_items` была пуста, а `sandbox_reader` не имел SELECT на учебные таблицы.
Позже владелец сообщил о выполнении `make fresh`: training seeds успешно применились,
а core seeds остановились на ошибке Flyway placeholders. Для seed-команд в Makefile
отключена подстановка placeholders: `${` внутри dollar-quoted JSON — часть SQL,
не переменная Flyway. Продолжение — `sudo make seed`, **не повторный fresh**.
В репозитории файл изображения с данным ключом также не найден. Docker API
недоступен текущему пользователю (permission denied); контейнеры не изменялись.

## Схема и результаты

Проверены миграции V1–V5 и оба seed-файла `analytics_training`.
V5 переименовывает первоначальную `order_items` в `retail_order_items`, сохраняя
FK на `orders`, `customers`, `products`, и создаёт отдельную старую учебную
`order_items` без этих FK. В `customers.customer_id` PRIMARY KEY, `city` допускает NULL.
`quantity > 0`, `unit_price >= 0`, статус — `completed`/`cancelled`.

На данных **файлов seeds**, без изменения работающей БД, подтверждены:
36/32/4 позиций, 17 завершённых заказов, 62 единицы, 302780 руб.; NULL-город — 460 руб.
Все семь SQL-примеров студенческого файла и три запроса преподавателя используют
`retail_order_items`; JOIN выполняется только с соответствующей `customers`.
Старые C101–C107 не смешиваются с C001–C012. Бесплатная позиция 28 сохраняется.
Задания используют только объяснённые GROUP BY, COUNT/SUM, WHERE, AS, ORDER BY и JOIN.

Эталонные SQL, ожидаемые столбцы/строки, шесть ID тестов и отдельные ответы:
[`solutions.json`](solutions.json). Этот файл **только для администратора**,
не для загрузки как содержимое урока. Ключ вариантов: **2, 3, 1, 4, 1, 3**.

| Задание | exercise_id / answer_id | Эталон | Статус |
|---|---|---|---|
| 1 | не подтверждены | assignments[0].code | локально проверен, не привязан |
| 2 | не подтверждены | assignments[1].code | локально проверен, не привязан |
| 3 | не подтверждены | assignments[2].code | локально проверен, не привязан |

## Режим самопроверки (без автоматического оценивания)

У существующего движка до аудита было автоматическое сравнение вывода с эталоном.
Оно не применяется к новым заданиям с `check_mode: "self_review"`.
Прежние Python/SQL-задания по умолчанию сохраняют прежний режим `graded`.
Схема БД не меняется: настройка хранится в существующем JSON `exercise_answers.answer`.

После успешного выполнения SELECT сервер сохраняет отдельный маркер
`__expert_review_exercises__`, не правильный ответ и не оценку. `is_correct=null`.
Это учитывается как выполненный обязательный запуск при ручном завершении урока;
шесть тестов по-прежнему требуют правильных ответов. Простое чтение ничего не завершает.
Ошибки SQL показываются отдельно и не открывают эталон. Код эталона не запускается
при сохранении в режиме самопроверки и не используется для сравнения результата.

`GET /courses/{slug}/modules/{module_id}/lessons/{lesson_id}/exercises/{exercise_id}/expert-solution`
проверяет сессию, доступ к опубликованному уроку, собственный успешный запуск и
точную пару `(lesson_id, exercise_id)`. До запуска — 403; чужое задание не открывается.
Ответ содержит только этот эталон, без служебного вывода. После перезагрузки
доступ восстанавливается из персональных попыток. Markdown остаётся без решений.

`id: none` получает внутренний `practice_sql_<строка>` в обоих парсерах.
Такое поле необязательно, не требует эталона и не открывает чужих решений.
Редактор пуст при первоначальном открытии. Для SQL кнопка называется «Выполнить SQL».
SQLRunner не изменён: только SELECT, approved-функции, public, READ ONLY,
`sandbox_reader` только к `analytics_training`, лимиты времени и вывода.

## Точные ручные действия владельца

1. Подтвердить, что используемый студенческий файл — нужная версия, либо предоставить
   отсутствующий `lesson_12_student.md`. Получить стабильный доступ к целевой БД.
2. Проверить/создать через существующую админку **черновик** SQL-урока в начальном
   курсе, модуль 4, позиция 2. Записать фактические course/module/lesson ID.
   Если для этого нужны миграции/seeds окружения, их проверяет и запускает владелец.
   Не применять весь `R__courses.sql` вслепую: там есть UPDATE существующих записей.
3. В редакторе урока загрузить студенческий Markdown. Удалить строки `id: none`
   **только в трёх обязательных блоках** и выйти из поля: существующая функция
   `ensureCodeExerciseIds` выдаст каждому редактору собственный ID. Это создание
   новых ссылок штатным workflow, а не подстановка выдуманных существующих ID.
4. В каждое соответствующее поле эталона вставить `assignments[0/1/2].code` из JSON.
   Для каждого включить «Самопроверка SQL: открыть эталон после запуска, без автоматического сравнения».
   Отметить в панели тестов варианты 2,3,1,4,1,3 и сохранить. В md отметки не уходят.
   Админка сохраняет ссылки и эталоны через существующий `code-content`, ответы
   тестов — через `/admin/lessons/{lesson_id}/exercises/{exercise_id}/answer`.
5. Получить **действительные** `exercise_id` и `answer_id` из БД:

   ```sql
   SELECT answer_id, lesson_id, exercise_id, answer
   FROM exercise_answers
   WHERE lesson_id = <фактический_id_SQL_урока>
   ORDER BY exercise_id;
   ```

   Связь редактора — строковый `exercise_id` в паре с `lesson_id`, **не** числовой
   PK `answer_id`. Проверить порядок задания 1→эталон 1, 2→2, 3→3.
6. Предоставить/найти реальный файл `m_45e57512f7eb46e0`, проверить объект MinIO,
   его content type, размеры и принадлежность курсу. Если metadata уже существует
   в другой целевой БД, подготовлен безопасный ручной [`link-image.sql`](link-image.sql):
   `psql … -v lesson_id=<реальный_ID> -f docs/lesson-12/link-image.sql`.
   Он не создаёт выдуманные metadata и отказывается работать без нужного урока/изображения.
   Здесь скрипт **не выполнялся**. Если metadata отсутствует, сначала нужен реальный
   файл и его штатная регистрация; нельзя угадать object_key или присвоить ключ чужому файлу.
7. Создать локальный `bindings.json` с фактическим `lesson_id` и тремя `exercise_ids`
   **по порядку заданий**. Выполнить из `backend/`:

   ```bash
   venv/bin/python -m scripts.prepare_lesson_12 --bindings bindings.json --output lesson12-package.json
   ```

   Инструмент только читает БД в READ ONLY. Проверяет принадлежность урока,
   существование трёх разных записей, точное соответствие SQL и режимов, связь
   изображения. Отказывается собирать пакет при `none`, перестановке эталонов,
   отсутствии реальных записей или изображения. Выводит связанные `content`,
   `solutions`, реальные `answer_id`; не публикует и не перезаписывает файлы/БД.
   Для API-сохранения брать только `content` и `solutions` и актуальный `version`
   из GET `code-content`, не отправлять целиком административный пакет.
8. После `fresh` проверить права `sandbox_reader`: удаление/создание public могло
   удалить прежние grants. Владелец может повторно применить существующий
   `infra/postgres/init/001_create_sandbox_user.sql` (сначала проверить его аудит):

   ```bash
   sudo docker compose exec -T postgres sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres' < infra/postgres/init/001_create_sandbox_user.sql
   ```

   Здесь эта команда **не запускалась**. После проверки реальных данных training и прав SELECT повторить три
   задания под студентом, проверить правильное изображение, ошибки, NULL-группу,
   отдельные эталоны и тесты. Обновить локальный md фактическими ID, затем публиковать.

## Воспроизводимые проверки

### Файлы реализации

- `backend/Makefile` — literal JSON в Flyway (`seed`, `ai-migrate`, `logs-migrate`), без изменения seed-записей.
- `backend/app/api/v1/schemas/exercises.py` — административный `check_mode` с прежним значением по умолчанию.
- `backend/app/api/v1/schemas/sandbox.py` — признаки самопроверки/доступности эталона в ответах API.
- `backend/app/api/v1/schemas/courses.py` — собственные выполненные запуски для восстановления интерфейса.
- `backend/app/api/v1/routes/sandbox.py` — передача этих признаков без раскрытия эталона.
- `backend/app/api/v1/services/lesson_code_content.py` — сохранение режима и AST-проверка SQL без запуска эталона.
- `backend/app/api/v1/services/sandbox.py` — self_review не вызывает grade, сохраняет отдельный маркер запуска.
- `backend/app/api/v1/services/student_exercises.py` — доступ к точному эталону после собственного запуска.
- `backend/app/api/v1/services/lesson_content.py` — безопасное восстановление собственных markers из успешных попыток.
- `backend/app/api/v1/services/lesson_completion.py` — обязательные запуски учитываются отдельно от тестов; practice исключён.
- `backend/app/models/enrollments_progress.py` — имя ключа JSONB, без изменений схемы.
- `backend/infra/minio/seeds/course-content/1/4/12.md` — описание самопроверки, пояснение вторичного ключа сортировки, понятный alt изображения.
- `backend/scripts/prepare_lesson_12.py` — сборка пакета только по существующим записям и правильному соответствию SQL.
- `backend/docs/lesson-12/solutions.json`, `link-image.sql`, `README.md` — административные материалы и ручные действия.
- `front/src/services/codeExercises.js` — сохранение режима при отправке эталонов администратором.
- `front/src/services/lessonCompletion.js` — обязательные запуски не подменяют ответы тестов, practice не блокирует урок.
- `front/src/pages/Admin/Lessons/LessonEditor.jsx` — выбор самопроверки и сохранение режима при правке SQL.
- `front/src/pages/Curses/Lesson.jsx` — состояние доступных после запуска эталонов и восстановление после открытия урока.
- `front/src/components/Markdown/Markdown.jsx`, `MarkdownBlocks.jsx`, `MarkdownCustomBlock.jsx` — передача персонального состояния через renderer.
- `front/src/components/Markdown/MarkdownCodeExercise.jsx` — пустой редактор, честные подписи, открытие эталона по разрешению сервера.
- `front/src/locales/admin/admin_ru.js`, `front/src/locales/courses/course_ru.js` — русские подписи режима и свободной практики.
- `backend/tests/test_lesson_12_sql.py`, `test_sql_self_review.py`, `test_seed_makefile.py` — новые проверки данных, режима, привязок и Flyway-команд.
- `backend/tests/test_student_exercises.py`, `test_lesson_code_content.py` — обновлён additive API-контракт без утечки кода.
- `front/tests/lesson12.test.js`, `front/tests/expertSolution.render.jsx` — три пустых редактора, отдельные эталоны и optional practice.

Не связанные с уроком изменения пользователя (admin logs и миграция V11) не редактировались.

```bash
venv/bin/python -m pytest tests/test_lesson_12_sql.py tests/test_sql_self_review.py -q
LESSON12_POSTGRES_TESTS=1 venv/bin/python -m pytest tests/test_lesson_12_sql.py -q
LESSON12_LIVE_DATA_TESTS=1 venv/bin/python -m pytest tests/test_lesson_12_sql.py -q
```

Вторая команда использует PostgreSQL **SELECT с VALUES-CTE из файлов seeds**,
в READ ONLY. Не создаёт таблиц и не применяет миграций. Это проверка PostgreSQL-семантики
на seed-фикстуре, **не** доказательство готовности текущих пустых таблиц/ACL песочницы.
На фронте: `node --test tests/lesson12.test.js`, `npm run test:render:expert-solution`.
Третья команда отдельно читает **реальные** training-таблицы под настроенной ролью
приложения в READ ONLY; она не проверяет и не исправляет grants SQL-песочницы.

### Фактически выполнено

- После `fresh` владельца реальные training-таблицы проверены read-only запросами:
  все три эталона и семь примеров совпали с seed-фикстурами PostgreSQL.
- Прямой запуск существующего `SQLRunner` под `sandbox_reader` вернул
  `permission denied for schema public`, `exit_code=1`, `success=false`.
  Это остаётся блокером реального выполнения студентом до восстановления ACL владельцем.
- Последний read-only запрос к core_db: целевой каталог уроков/эталоны урока 12/
  metadata изображения не обнаружены (core seeds остановились до заполнения).
- Расширенный набор backend: **198 passed, 1 skipped**. Пропущен отдельный
  opt-in SQLRunner integration test (`SANDBOX_SQL_TESTS` не включён);
  фактический отказ прав SQLRunner проверен отдельным read-only запуском выше.
- `node --test tests/lesson12.test.js tests/codeExercises.test.js tests/lessonCompletion.test.js tests/i18n.test.js tests/admin.test.js`:
  **27 passed**.
- `npm test`: **96 passed, 1 failed**. Не связанная с уроком ошибка
  `tests/descriptionPreview.test.js` (обрезка превью). Этот код не менялся.
- `npm run test:render:expert-solution`, `npm run test:render:single-choice`,
  `npm run build` — успешно; сборка предупреждает о chunk >500 KB.
- Выборочный oxlint — без ошибок, с прежними предупреждениями set-state-in-effect.
- `venv/bin/python -m scripts.prepare_lesson_12 --help` — успешно.
  Публикационный пакет без реальных привязок не собирался.
- `test_seed_makefile.py` проверяет три Flyway-команды через mock Docker:
  `placeholderReplacement=false` передаётся во всех путях, читающих seeds.
  Реальный Flyway/Docker не запускался агентом, `fresh` не повторялся.

Полный запуск backend-проверок:

```bash
LESSON12_POSTGRES_TESTS=1 LESSON12_LIVE_DATA_TESTS=1 venv/bin/python -m pytest tests/test_lesson_12_sql.py tests/test_sql_self_review.py tests/test_lesson_11_sql.py tests/test_practice_submission.py tests/test_sql_runner.py tests/test_analytics_training_sql.py tests/test_expert_solution.py tests/test_student_exercises.py tests/test_lesson_code_content.py tests/test_lesson_completion.py tests/test_markdown_parser.py tests/test_seed_makefile.py -q -rs
```
