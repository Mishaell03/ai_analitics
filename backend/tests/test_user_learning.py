"""Интеграционные тесты пользовательского обучения.

Проверяют список курсов текущего пользователя и выбор следующего урока.
Тестам нужны поднятые PostgreSQL и MinIO: как и остальные интеграционные
тесты проекта, они пропускаются, если инфраструктура недоступна.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import delete

import app.main  # noqa: F401  (регистрация всех моделей)

from app.core.database import AsyncSessionLocal
from app.core.tokens import hash_session_token
from app.main import app
from app.models.auth import UserSession
from app.models.courses import Course, CourseModule, Lesson
from app.models.enrollments_progress import CourseEnrollment, LessonAttempt
from app.models.users import User

from conftest import LOOP, infrastructure_available


pytestmark = pytest.mark.skipif(
    not infrastructure_available(),
    reason="нужны поднятые PostgreSQL и MinIO",
)


def run(coroutine):
    """ЗАПУСКАЕТ КОРУТИНУ В СИНХРОННОМ ТЕСТЕ"""

    return LOOP.run_until_complete(coroutine)


async def _create_user(db, email: str, now: datetime) -> tuple[User, str]:
    """СОЗДАЁТ ИЗОЛИРОВАННОГО ПОЛЬЗОВАТЕЛЯ С СЕССИЕЙ"""

    user = User(
        name="Pytest Learning",
        email=email,
        is_admin=False,
        is_blocked=False,
    )

    db.add(user)
    await db.flush()

    token = f"pytest-learning-{uuid.uuid4().hex}"

    db.add(
        UserSession(
            user_id=user.user_id,
            # в базе лежит только хэш, как и у настоящей сессии
            session=hash_session_token(token),
            ip="127.0.0.1",
            language="en",
            provider="pass",
            platform="web",
            device_name="pytest",
            device_id=f"pytest-{uuid.uuid4().hex[:24]}",
            expires_at=now + timedelta(days=1),
        )
    )

    return user, token


@pytest.fixture
def learning():
    """ИЗОЛИРОВАННЫЙ КУРС, ПОЛЬЗОВАТЕЛИ И ИХ ЗАПИСИ"""

    suffix = uuid.uuid4().hex[:10]
    state = SimpleNamespace()

    async def setup():
        now = datetime.now(timezone.utc)

        async with AsyncSessionLocal() as db:
            user, user_token = await _create_user(
                db,
                email=f"pytest-learning-{suffix}@example.com",
                now=now,
            )
            other_user, other_token = await _create_user(
                db,
                email=f"pytest-learning-other-{suffix}@example.com",
                now=now,
            )
            no_courses_user, no_courses_token = await _create_user(
                db,
                email=f"pytest-learning-empty-{suffix}@example.com",
                now=now,
            )

            course = Course(
                slug=f"pytest-learning-{suffix}",
                title="Pytest learning course",
                description="Курс для проверки продолжения обучения",
                is_published=True,
            )
            empty_course = Course(
                slug=f"pytest-learning-empty-{suffix}",
                title="Pytest empty course",
                description="Курс без уроков",
                is_published=True,
            )
            other_course = Course(
                slug=f"pytest-learning-other-{suffix}",
                title="Pytest other course",
                description="Чужой курс",
                is_published=True,
            )
            unpublished_course = Course(
                slug=f"pytest-learning-hidden-{suffix}",
                title="Pytest hidden course",
                description="Неопубликованный курс",
                is_published=False,
            )

            db.add_all([course, empty_course, other_course, unpublished_course])
            await db.flush()

            module_1 = CourseModule(
                course_id=course.course_id,
                title="Module 1",
                position=1,
                is_published=True,
            )
            module_2 = CourseModule(
                course_id=course.course_id,
                title="Module 2",
                position=2,
                is_published=True,
            )
            unpublished_module = CourseModule(
                course_id=course.course_id,
                title="Hidden module",
                position=3,
                is_published=False,
            )
            module_4 = CourseModule(
                course_id=course.course_id,
                title="Module 4",
                position=4,
                is_published=True,
            )

            other_module = CourseModule(
                course_id=other_course.course_id,
                title="Other module",
                position=1,
                is_published=True,
            )

            db.add_all([
                module_1,
                module_2,
                unpublished_module,
                module_4,
                other_module,
            ])
            await db.flush()

            lesson_1 = Lesson(module_id=module_1.module_id, title="Lesson 1", position=1, is_published=True)
            lesson_2 = Lesson(module_id=module_1.module_id, title="Lesson 2", position=2, is_published=True)
            lesson_3 = Lesson(module_id=module_1.module_id, title="Lesson 3", position=3, is_published=True)
            lesson_4 = Lesson(module_id=module_2.module_id, title="Lesson 4", position=1, is_published=True)
            lesson_5 = Lesson(module_id=module_2.module_id, title="Lesson 5", position=2, is_published=True)
            # урок лежит в неопубликованном модуле
            lesson_hidden_module = Lesson(
                module_id=unpublished_module.module_id,
                title="Hidden module lesson",
                position=1,
                is_published=True,
            )
            # урок не опубликован, хотя модуль опубликован
            lesson_unpublished = Lesson(
                module_id=module_4.module_id,
                title="Unpublished lesson",
                position=1,
                is_published=False,
            )
            lesson_8 = Lesson(module_id=module_4.module_id, title="Lesson 8", position=2, is_published=True)

            other_lesson = Lesson(
                module_id=other_module.module_id,
                title="Other lesson",
                position=1,
                is_published=True,
            )

            db.add_all([
                lesson_1,
                lesson_2,
                lesson_3,
                lesson_4,
                lesson_5,
                lesson_hidden_module,
                lesson_unpublished,
                lesson_8,
                other_lesson,
            ])
            await db.flush()

            db.add_all([
                CourseEnrollment(
                    user_id=user.user_id,
                    course_id=course.course_id,
                    created_at=now - timedelta(days=2),
                ),
                CourseEnrollment(
                    user_id=user.user_id,
                    course_id=empty_course.course_id,
                    created_at=now - timedelta(days=3),
                ),
                CourseEnrollment(
                    user_id=user.user_id,
                    course_id=unpublished_course.course_id,
                    created_at=now,
                ),
                CourseEnrollment(
                    user_id=other_user.user_id,
                    course_id=other_course.course_id,
                    created_at=now,
                ),
                CourseEnrollment(
                    user_id=other_user.user_id,
                    course_id=course.course_id,
                    created_at=now - timedelta(days=4),
                ),
            ])

            await db.commit()

            state.user_id = user.user_id
            state.user_token = user_token
            state.other_user_id = other_user.user_id
            state.other_user_token = other_token
            state.no_courses_user_id = no_courses_user.user_id
            state.no_courses_token = no_courses_token

            state.course_id = course.course_id
            state.course_slug = course.slug
            state.empty_course_id = empty_course.course_id
            state.empty_course_slug = empty_course.slug
            state.other_course_id = other_course.course_id
            state.other_course_slug = other_course.slug
            state.unpublished_course_id = unpublished_course.course_id
            state.unpublished_course_slug = unpublished_course.slug

            state.lesson_ids = {
                "lesson_1": lesson_1.lesson_id,
                "lesson_2": lesson_2.lesson_id,
                "lesson_3": lesson_3.lesson_id,
                "lesson_4": lesson_4.lesson_id,
                "lesson_5": lesson_5.lesson_id,
                "hidden_module": lesson_hidden_module.lesson_id,
                "unpublished": lesson_unpublished.lesson_id,
                "lesson_8": lesson_8.lesson_id,
            }
            state.other_lesson_id = other_lesson.lesson_id
            state.visible_lesson_ids = [
                lesson_1.lesson_id,
                lesson_2.lesson_id,
                lesson_3.lesson_id,
                lesson_4.lesson_id,
                lesson_5.lesson_id,
                lesson_8.lesson_id,
            ]

    run(setup())

    yield state

    async def cleanup():
        async with AsyncSessionLocal() as db:
            # удаляем только созданные тестом сущности; остальное
            # (попытки, записи, сессии, события) уходит каскадом
            await db.execute(
                delete(Course).where(
                    Course.course_id.in_([
                        state.course_id,
                        state.empty_course_id,
                        state.other_course_id,
                        state.unpublished_course_id,
                    ])
                )
            )
            await db.execute(
                delete(User).where(
                    User.user_id.in_([
                        state.user_id,
                        state.other_user_id,
                        state.no_courses_user_id,
                    ])
                )
            )
            await db.commit()

    run(cleanup())


@pytest.fixture
def api_client():
    """ФАБРИКА HTTP-КЛИЕНТОВ С СЕССИОННОЙ COOKIE"""

    clients = []

    def make(token: str | None = None):
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )

        if token is not None:
            client.cookies.set("session_token", token)

        clients.append(client)

        return client

    yield make

    async def close():
        for client in clients:
            await client.aclose()

    run(close())


def add_attempt(user_id: int, lesson_id: int, correctness: int = 3):
    """СОЗДАЁТ ПОПЫТКУ РЕШЕНИЯ УРОКА"""

    async def scenario():
        async with AsyncSessionLocal() as db:
            db.add(
                LessonAttempt(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    correctness=correctness,
                    speed=1,
                )
            )
            await db.commit()

    run(scenario())


def request(client, path: str, **kwargs):
    """ВЫПОЛНЯЕТ HTTP-ЗАПРОС В ОБЩЕМ EVENT LOOP"""

    async def scenario():
        return await client.get(path, **kwargs)

    return run(scenario())


def get_next_lesson(client, course_slug: str):
    """ЗАПРАШИВАЕТ СЛЕДУЮЩИЙ УРОК"""

    return request(client, f"/api/v1/courses/{course_slug}/next-lesson")


# ---------- КУРСЫ ПОЛЬЗОВАТЕЛЯ ----------

def test_my_courses_returns_only_own_enrollments(learning, api_client):
    """ПОЛЬЗОВАТЕЛЬ ПОЛУЧАЕТ ТОЛЬКО СВОИ ОПУБЛИКОВАННЫЕ КУРСЫ"""

    client = api_client(learning.user_token)

    response = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page_size": 100},
    )

    assert response.status_code == 200

    body = response.json()
    slugs = [course["slug"] for course in body["courses"]]

    # сначала более поздняя запись, затем более ранняя
    assert slugs == [
        learning.course_slug,
        learning.empty_course_slug,
    ]

    assert learning.other_course_slug not in slugs
    assert learning.unpublished_course_slug not in slugs
    assert all(course["is_enrolled"] is True for course in body["courses"])
    assert body["total_pages"] == 1
    assert body["current_page"] == 1
    assert body["page_size"] == 100


def test_my_courses_ignores_foreign_user_id(learning, api_client):
    """ЧУЖОЙ user_id В QUERY НЕ ДАЁТ ДОСТУП К ЧУЖИМ КУРСАМ"""

    client = api_client(learning.user_token)

    response = request(
        client,
        "/api/v1/courses",
        params={
            "enrolled_only": True,
            "user_id": learning.other_user_id,
            "page_size": 100,
        },
    )

    assert response.status_code == 200

    slugs = [course["slug"] for course in response.json()["courses"]]

    assert set(slugs) == {
        learning.course_slug,
        learning.empty_course_slug,
    }
    assert learning.other_course_slug not in slugs


def test_my_courses_empty_list(learning, api_client):
    """ПОЛЬЗОВАТЕЛЬ БЕЗ ЗАПИСЕЙ ПОЛУЧАЕТ ПУСТОЙ СПИСОК"""

    client = api_client(learning.no_courses_token)

    response = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["courses"] == []
    assert body["total_pages"] == 0
    assert body["current_page"] == 1
    assert body["page_size"] == 20


def test_my_courses_pagination_is_stable(learning, api_client):
    """КУРСЫ ПАГИНИРУЮТСЯ В ПОРЯДКЕ ДАТЫ ЗАПИСИ"""

    client = api_client(learning.user_token)

    first_page = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page": 1, "page_size": 1},
    )

    second_page = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page": 2, "page_size": 1},
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_body = first_page.json()
    second_body = second_page.json()

    assert first_body["total_pages"] == 2
    assert first_body["courses"][0]["slug"] == learning.course_slug
    assert second_body["courses"][0]["slug"] == learning.empty_course_slug


def test_my_courses_excludes_without_enrollment_row(learning, api_client):
    """УДАЛЁННАЯ ЗАПИСЬ НА КУРС СРАЗУ УБИРАЕТ КУРС"""

    async def unenroll():
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(CourseEnrollment).where(
                    CourseEnrollment.user_id == learning.user_id,
                    CourseEnrollment.course_id == learning.empty_course_id,
                )
            )
            await db.commit()

    run(unenroll())

    client = api_client(learning.user_token)
    response = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page_size": 100},
    )

    assert response.status_code == 200

    slugs = [course["slug"] for course in response.json()["courses"]]

    assert learning.empty_course_slug not in slugs
    assert learning.course_slug in slugs


def test_courses_default_mode_keeps_catalog_behavior(learning, api_client):
    """ФЛАГ enrolled_only НЕ МЕНЯЕТ ПРЕЖНИЙ КАТАЛОГ КУРСОВ"""

    client = api_client(learning.user_token)

    response = request(
        client,
        "/api/v1/courses",
        params={"page_size": 100},
    )

    assert response.status_code == 200

    courses = {
        course["slug"]: course
        for course in response.json()["courses"]
    }

    assert learning.course_slug in courses
    assert learning.other_course_slug in courses
    assert learning.unpublished_course_slug not in courses
    assert courses[learning.course_slug]["is_enrolled"] is True
    assert courses[learning.other_course_slug]["is_enrolled"] is False


def test_my_courses_requires_authentication(api_client):
    """БЕЗ СЕССИИ СПИСОК КУРСОВ НЕДОСТУПЕН"""

    client = api_client()

    response = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_SESSION"


# ---------- ПРОДОЛЖЕНИЕ ОБУЧЕНИЯ ----------

def test_next_lesson_starts_from_first_available(learning, api_client):
    """НОВЫЙ УЧЕНИК НАЧИНАЕТ С ПЕРВОГО ДОСТУПНОГО УРОКА"""

    client = api_client(learning.user_token)

    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["course"]["slug"] == learning.course_slug
    assert body["last_completed_lesson"] is None
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_1"]
    assert body["next_lesson"]["module_id"] > 0
    assert body["next_lesson"]["module_title"] == "Module 1"
    assert body["is_course_completed"] is False
    assert body["lessons_total"] == 6
    assert body["lessons_completed"] == 0


def test_next_lesson_after_one_completed(learning, api_client):
    """ПОСЛЕ ЗАВЕРШЁННОГО УРОКА ВОЗВРАЩАЕТСЯ СЛЕДУЮЩИЙ ПО ПОРЯДКУ"""

    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"])

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_1"]
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_2"]
    assert body["lessons_completed"] == 1
    assert body["is_course_completed"] is False


def test_next_lesson_after_several_completed(learning, api_client):
    """ПОСЛЕ НЕСКОЛЬКИХ УРОКОВ ВЫБИРАЕТСЯ СЛЕДУЮЩИЙ ЗА ПОСЛЕДНИМ"""

    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"])
    add_attempt(learning.user_id, learning.lesson_ids["lesson_2"])

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_2"]
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_3"]
    assert body["lessons_completed"] == 2


def test_wrong_attempt_is_not_completion(learning, api_client):
    """ПОПЫТКА БЕЗ МАКСИМАЛЬНОЙ ОЦЕНКИ НЕ СЧИТАЕТСЯ ЗАВЕРШЕНИЕМ"""

    add_attempt(
        learning.user_id,
        learning.lesson_ids["lesson_1"],
        correctness=2,
    )

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["last_completed_lesson"] is None
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_1"]
    assert body["lessons_completed"] == 0


def test_next_lesson_with_gap_returns_first_incomplete(learning, api_client):
    """ПРИ ПРОПУСКЕ ПРОДОЛЖЕНИЕ ВОЗВРАЩАЕТ ПЕРВЫЙ НЕЗАВЕРШЁННЫЙ УРОК"""

    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"])
    add_attempt(learning.user_id, learning.lesson_ids["lesson_3"])

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    # последний завершённый по порядку — lesson_3, но продолжение
    # возвращает первый пропущенный урок, а не следующий за последним.
    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_3"]
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_2"]
    assert body["lessons_completed"] == 2


def test_successful_attempt_survives_later_failed_attempt(learning, api_client):
    """ПОЗДНЯЯ НЕУДАЧНАЯ ПОПЫТКА НЕ ОТМЕНЯЕТ ЗАВЕРШЕНИЕ УРОКА"""

    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"], correctness=3)
    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"], correctness=1)

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200
    body = response.json()
    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_1"]
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_2"]
    assert body["lessons_completed"] == 1


def test_next_lesson_skips_unpublished_lessons_and_modules(learning, api_client):
    """НЕОПУБЛИКОВАННЫЕ УРОКИ И МОДУЛИ НЕ ПОПАДАЮТ В ПРОДОЛЖЕНИЕ"""

    for key in ("lesson_1", "lesson_2", "lesson_3", "lesson_4", "lesson_5"):
        add_attempt(learning.user_id, learning.lesson_ids[key])

    # даже завершённые уроки вне опубликованного контента не учитываются
    add_attempt(learning.user_id, learning.lesson_ids["hidden_module"])
    add_attempt(learning.user_id, learning.lesson_ids["unpublished"])

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    # hidden_module и unpublished-урок пропущены
    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_5"]
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_8"]
    assert body["lessons_total"] == len(learning.visible_lesson_ids)
    assert body["lessons_completed"] == 5


def test_next_lesson_after_last_lesson_marks_course_completed(learning, api_client):
    """ЗАВЕРШЕНИЕ ПОСЛЕДНЕГО ДОСТУПНОГО УРОКА ЗАВЕРШАЕТ КУРС"""

    for lesson_id in learning.visible_lesson_ids[:-1]:
        add_attempt(learning.user_id, lesson_id)

    client = api_client(learning.user_token)

    before_last = get_next_lesson(client, learning.course_slug)

    assert before_last.status_code == 200
    assert before_last.json()["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_8"]
    assert before_last.json()["is_course_completed"] is False

    add_attempt(learning.user_id, learning.lesson_ids["lesson_8"])

    after_last = get_next_lesson(client, learning.course_slug)

    assert after_last.status_code == 200

    body = after_last.json()

    assert body["last_completed_lesson"]["lesson_id"] == learning.lesson_ids["lesson_8"]
    assert body["next_lesson"] is None
    assert body["is_course_completed"] is True
    assert body["lessons_completed"] == body["lessons_total"]


def test_next_lesson_course_without_lessons(learning, api_client):
    """КУРС БЕЗ УРОКОВ ОБРАБАТЫВАЕТСЯ БЕЗ ОШИБКИ"""

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.empty_course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["last_completed_lesson"] is None
    assert body["next_lesson"] is None
    assert body["is_course_completed"] is False
    assert body["lessons_total"] == 0
    assert body["lessons_completed"] == 0


def test_next_lesson_unknown_course(learning, api_client):
    """НЕСУЩЕСТВУЮЩИЙ КУРС ДАЁТ COURSE_NOT_FOUND"""

    client = api_client(learning.user_token)
    response = get_next_lesson(client, "pytest-course-does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COURSE_NOT_FOUND"


def test_next_lesson_unpublished_course(learning, api_client):
    """НЕОПУБЛИКОВАННЫЙ КУРС НЕДОСТУПЕН"""

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.unpublished_course_slug)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COURSE_NOT_PUBLISHED"


def test_next_lesson_requires_enrollment(learning, api_client):
    """ПОЛЬЗОВАТЕЛЬ БЕЗ ЗАПИСИ НА КУРС НЕ ПОЛУЧАЕТ ПРОГРЕСС"""

    client = api_client(learning.no_courses_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "COURSE_NOT_ENROLLED"


def test_next_lesson_does_not_leak_other_user_progress(learning, api_client):
    """ПРОГРЕСС ДРУГОГО ПОЛЬЗОВАТЕЛЯ НЕ ВЛИЯЕТ НА ОТВЕТ"""

    add_attempt(learning.other_user_id, learning.lesson_ids["lesson_1"])
    add_attempt(learning.other_user_id, learning.lesson_ids["lesson_2"])

    client = api_client(learning.user_token)
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 200

    body = response.json()

    assert body["last_completed_lesson"] is None
    assert body["next_lesson"]["lesson_id"] == learning.lesson_ids["lesson_1"]
    assert body["lessons_completed"] == 0


def test_next_lesson_requires_authentication(learning, api_client):
    """БЕЗ СЕССИИ ПРОДОЛЖЕНИЕ ОБУЧЕНИЯ НЕДОСТУПНО"""

    client = api_client()
    response = get_next_lesson(client, learning.course_slug)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "INVALID_SESSION"


def test_completion_status_is_returned_for_courses_modules_and_lessons(learning, api_client):
    """СТАТУСЫ ЗАВЕРШЕНИЯ ВЕРНЫ ДЛЯ УРОКА, МОДУЛЯ И КУРСА."""

    add_attempt(learning.user_id, learning.lesson_ids["lesson_1"])
    client = api_client(learning.user_token)

    course_response = request(
        client,
        f"/api/v1/courses/{learning.course_slug}",
        params={"page_size": 100},
    )
    assert course_response.status_code == 200
    modules = course_response.json()["modules"]
    module_1 = next(module for module in modules if module["title"] == "Module 1")
    assert module_1["is_completed"] is False
    assert module_1["lessons_completed"] == 1
    assert module_1["lessons_total"] == 3

    lessons_response = request(
        client,
        f"/api/v1/courses/{learning.course_slug}/modules/{module_1['module_id']}",
    )
    assert lessons_response.status_code == 200
    lessons_body = lessons_response.json()
    assert lessons_body["module"]["is_completed"] is False
    completed = {
        lesson["lesson_id"]: lesson["is_completed"]
        for lesson in lessons_body["lessons"]
    }
    assert completed[learning.lesson_ids["lesson_1"]] is True
    assert completed[learning.lesson_ids["lesson_2"]] is False

    lesson_response = request(
        client,
        f"/api/v1/courses/{learning.course_slug}/modules/{module_1['module_id']}"
        f"/lessons/{learning.lesson_ids['lesson_1']}",
    )
    assert lesson_response.status_code == 200
    assert lesson_response.json()["lesson"]["is_completed"] is True

    profile_response = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page_size": 100},
    )
    profile_course = next(
        item for item in profile_response.json()["courses"]
        if item["slug"] == learning.course_slug
    )
    assert profile_course["is_course_completed"] is False
    assert profile_course["lessons_completed"] == 1
    assert profile_course["lessons_total"] == 6

    for lesson_id in learning.visible_lesson_ids[1:]:
        add_attempt(learning.user_id, lesson_id)

    fully_completed = request(
        client,
        f"/api/v1/courses/{learning.course_slug}",
        params={"page_size": 100},
    )
    assert all(module["is_completed"] for module in fully_completed.json()["modules"])

    completed_profile = request(
        client,
        "/api/v1/courses",
        params={"enrolled_only": True, "page_size": 100},
    )
    completed_course = next(
        item for item in completed_profile.json()["courses"]
        if item["slug"] == learning.course_slug
    )
    assert completed_course["is_course_completed"] is True
    assert completed_course["lessons_completed"] == completed_course["lessons_total"]


def test_course_catalog_search_ranks_exact_and_fuzzy_matches(learning, api_client):
    client = api_client(learning.user_token)

    exact_response = request(
        client,
        "/api/v1/courses",
        params={"q": "Pytest learning course", "page_size": 100},
    )
    assert exact_response.status_code == 200
    exact_slugs = [item["slug"] for item in exact_response.json()["courses"]]
    assert exact_slugs[0] == learning.course_slug

    typo_response = request(
        client,
        "/api/v1/courses",
        params={"q": "pytes learning cours", "page_size": 100},
    )
    assert typo_response.status_code == 200
    typo_slugs = [item["slug"] for item in typo_response.json()["courses"]]
    assert learning.course_slug in typo_slugs

    empty_response = request(
        client,
        "/api/v1/courses",
        params={"q": "   ", "page_size": 100},
    )
    assert empty_response.status_code == 200
    assert empty_response.json()["total_pages"] >= 1


def test_course_catalog_enrollment_filters(learning, api_client):
    client = api_client(learning.user_token)

    enrolled_response = request(
        client,
        "/api/v1/courses",
        params={"enrollment_filter": "enrolled", "page_size": 100},
    )
    not_enrolled_response = request(
        client,
        "/api/v1/courses",
        params={"enrollment_filter": "not_enrolled", "page_size": 100},
    )
    assert enrolled_response.status_code == 200
    assert not_enrolled_response.status_code == 200

    enrolled_slugs = {item["slug"] for item in enrolled_response.json()["courses"]}
    not_enrolled_slugs = {item["slug"] for item in not_enrolled_response.json()["courses"]}
    assert learning.course_slug in enrolled_slugs
    assert learning.course_slug not in not_enrolled_slugs
    assert enrolled_slugs.isdisjoint(not_enrolled_slugs)
