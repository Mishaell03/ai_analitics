"""Собрать пакет урока только из реально сохранённых эталонов. БД — READ ONLY.

Запуск: venv/bin/python -m scripts.prepare_lesson_12 --bindings bindings.json --output package.json
bindings.json: {"lesson_id": <реальный ID>, "exercise_ids": [<ID задания 1>, <ID 2>, <ID 3>]}
Никаких ID, записей БД, файлов MinIO или миграций этот инструмент не создаёт.
"""

import argparse
import asyncio
import json
from pathlib import Path
import re

import asyncpg
from pglast import parse_sql
from pglast.stream import RawStream
from sqlalchemy.engine import make_url

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/lesson-12/solutions.json"
SOURCE = ROOT / "infra/minio/seeds/course-content/1/4/12.md"


def normalized_sql(code):
    return RawStream()(parse_sql(code))


def prepare_content(source, assignments, references):
    """Порядок обязательных редакторов должен совпадать с порядком трёх эталонов."""
    slots = list(re.finditer(r"^:::code sql\n(?:id: [A-Za-z0-9_-]+\n)?:::[ \t]*$", source, re.M))
    if len(slots) != 3 or len(assignments) != 3 or len(references) != 3:
        raise ValueError("Ожидалось ровно три обязательных SQL-редактора и три эталона")
    ids = [row["exercise_id"] for row in references]
    if len(set(ids)) != 3 or any(
        not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) or value in {"none", "reference"}
        or value.startswith("practice_") for value in ids
    ):
        raise ValueError("Нужны три разных существующих ID обязательных заданий")
    for assignment, row in zip(assignments, references):
        answer = json.loads(row["answer"])
        if (not row.get("answer_id") or answer.get("type") != "code"
                or answer.get("language") != "sql" or answer.get("check_mode") != "self_review"
                or normalized_sql(answer.get("value", "")) != normalized_sql(assignment["code"])):
            raise ValueError(f"Эталон задания {assignment['number']} не совпадает с материалами преподавателя")
    for slot, exercise_id in reversed(list(zip(slots, ids))):
        source = source[:slot.start()] + f":::code sql\nid: {exercise_id}\n:::" + source[slot.end():]
    return source


async def prepare(bindings):
    manifest = json.loads(MANIFEST.read_text())
    lesson_id = bindings["lesson_id"]
    ids = bindings["exercise_ids"]
    if not isinstance(lesson_id, int) or lesson_id < 1 or len(ids) != 3:
        raise ValueError("Укажите реальный lesson_id и три ID из административного API")
    url = make_url(settings.database_url)
    conn = await asyncpg.connect(host=url.host, port=url.port or 5432, user=url.username,
                                 password=url.password, database=url.database, timeout=5)
    try:
        async with conn.transaction(readonly=True):
            target = await conn.fetchrow("""
                SELECT l.lesson_id FROM lessons l
                JOIN course_modules m USING (module_id) JOIN courses c USING (course_id)
                WHERE l.lesson_id=$1 AND c.slug=$2 AND m.position=$3 AND l.position=$4
            """, lesson_id, manifest["course_slug"], manifest["module_position"], manifest["lesson_position"])
            if target is None:
                raise ValueError("Целевой урок не найден в модуле 4 курса «Аналитика данных с нуля». Не подставляйте ID 12 вслепую")
            records = await conn.fetch("""
                SELECT answer_id, exercise_id, answer FROM exercise_answers
                WHERE lesson_id=$1 AND exercise_id=ANY($2::text[])
            """, lesson_id, ids)
            by_id = {row["exercise_id"]: dict(row) for row in records}
            if any(exercise_id not in by_id for exercise_id in ids):
                raise ValueError("Не все три эталона реально сохранены в exercise_answers целевого урока")
            references = [by_id[exercise_id] for exercise_id in ids]
            content = prepare_content(SOURCE.read_text(), manifest["assignments"], references)
            image = await conn.fetchval("""
                SELECT m.media_id FROM media_files m JOIN lesson_media lm USING (media_id)
                JOIN lessons l ON l.lesson_id=lm.lesson_id
                JOIN course_modules cm ON cm.module_id=l.module_id
                WHERE lm.lesson_id=$1 AND m.media_key=$2 AND m.course_id=cm.course_id AND m.kind='image'
            """, lesson_id, manifest["media_key"])
            if image is None:
                raise ValueError("Изображение m_45e57512f7eb46e0 не зарегистрировано или не связано с целевым уроком")
            return {
                "lesson_id": lesson_id, "content": content,
                "solutions": [{"exercise_id": row["exercise_id"], "language": "sql",
                               "code": item["code"], "check_mode": "self_review"}
                              for item, row in zip(manifest["assignments"], references)],
                "mapping": [{"assignment": item["number"], "exercise_id": row["exercise_id"],
                             "answer_id": row["answer_id"]}
                            for item, row in zip(manifest["assignments"], references)],
            }
    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = asyncio.run(prepare(json.loads(args.bindings.read_text())))
    except (ValueError, KeyError, TypeError, asyncpg.PostgresError, OSError) as exc:
        parser.exit(1, f"Пакет не собран: {type(exc).__name__}: {exc}\n")
    # Не затираем ранее подготовленные материалы.
    with args.output.open("x") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(f"Пакет подготовлен: {args.output}. Ничего не опубликовано и не изменено в БД.")


if __name__ == "__main__":
    main()
