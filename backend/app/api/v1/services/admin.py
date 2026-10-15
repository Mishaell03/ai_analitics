import asyncio
from datetime import date, datetime, timezone

from fastapi import Request
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin import (
    AdminQuantityUsers,
    AdminUserAuthMethod,
    AdminUserConsent,
    AdminUserCourseProgress,
    AdminUserDetail,
    AdminUserItem,
    AdminUserLearningStats,
    AdminUserLessonAttempt,
    AdminUserSession,
    DashboardLatestUser,
    DashboardResponse,
    DashboardTopCourse,
)
from app.core.avatars import get_avatar_url
from app.core.errors import raise_backend_error
from app.core.pagination import get_pagination, get_total_pages
from app.models.auth import Provider, UserAuthMethod, UserSession
from app.models.courses import Course, CourseModule, Lesson
from app.models.enrollments_progress import CourseEnrollment, LessonAttempt
from app.models.errors import UserEventLog
from app.models.users import User, UserConsent


# верх шкалы correctness (CHECK 0..3): урок с такой попыткой считается решённым
SOLVED_CORRECTNESS = 3

# сколько последних попыток отдаём в карточке пользователя
RECENT_ATTEMPTS_LIMIT = 20


def is_active_session():
    """Условие активной сессии.

    Те же правила, что и в app.core.session.get_current_user:
    сессия не отозвана и ещё не истекла.
    """
    now = datetime.now(timezone.utc)

    return (
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > now,
    )


def as_ip(value) -> str | None:
    """IP СТРОКОЙ

    Колонки INET драйвер отдаёт как ipaddress.IPv4Address,
    а в ответе наружу уходит строка.
    """

    return str(value) if value is not None else None


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(
            self,
            users: int | None = 5,
            top_courses: int | None = 5,
            # period: int | None = 14,
            # date_of: date | None = None,
            # date_to: date | None = None,
    ) -> DashboardResponse:
        """COUNTERS OF THE MAIN TABLES, LAST REGISTERED USERS AND TOP COURSES"""

        totals = await self._get_totals()
        latest_users = await self._get_latest_users(users_count=users)
        top_courses = await self._get_top_courses(top_courses=top_courses)

        return DashboardResponse(
            total_users=totals["total_users"],
            total_courses=totals["total_courses"],
            total_lessons=totals["total_lessons"],
            total_enrollments=totals["total_enrollments"],
            total_active_sessions=totals["total_active_sessions"],
            latest_users=latest_users,
            top_courses=top_courses,
        )

    async def _get_totals(self) -> dict[str, int]:
        """Все счётчики одним запросом через скалярные подзапросы."""

        counters = {
            "total_users": select(func.count(User.user_id)).scalar_subquery(),
            "total_courses": select(func.count(Course.course_id)).scalar_subquery(),
            "total_lessons": select(func.count(Lesson.lesson_id)).scalar_subquery(),
            "total_enrollments": select(func.count(CourseEnrollment.enrollment_id)).scalar_subquery(),
            "total_active_sessions": select(func.count(UserSession.id))
            .where(*is_active_session())
            .scalar_subquery(),
        }

        result = await self.db.execute(
            select(
                counters["total_users"].label("total_users"),
                counters["total_courses"].label("total_courses"),
                counters["total_lessons"].label("total_lessons"),
                counters["total_enrollments"].label("total_enrollments"),
                counters["total_active_sessions"].label("total_active_sessions"),
            )
        )

        row = result.one()

        return {
            "total_users": row.total_users,
            "total_courses": row.total_courses,
            "total_lessons": row.total_lessons,
            "total_enrollments": row.total_enrollments,
            "total_active_sessions": row.total_active_sessions,
        }

    async def _get_latest_users(self, users_count: int) -> list[DashboardLatestUser]:
        result = await self.db.execute(
            select(
                User.user_id,
                User.name,
                User.email,
                User.img,
                User.is_default_img,
                User.created_at,
            )
            .order_by(User.created_at.desc(), User.user_id.desc())
            .limit(users_count)
        )

        rows = result.all()

        # на каждый аватар уходит stat + presign, поэтому подписываем параллельно
        img_urls = await asyncio.gather(*(
            get_avatar_url(img=img, is_default_img=bool(is_default_img))
            for _, _, _, img, is_default_img, _ in rows
        ))

        return [
            DashboardLatestUser(
                user_id=user_id,
                name=name,
                email=email,
                created_at=created_at,
                img_url=img_url,
            )
            for (user_id, name, email, _, _, created_at), img_url in zip(rows, img_urls)
        ]

    async def _get_top_courses(self, top_courses: int) -> list[DashboardTopCourse]:
        """Курсы по количеству записей, подсчёт на стороне БД.

        LEFT JOIN оставляет курсы без записей — они попадут в конец
        рейтинга с нулевым количеством, если активных курсов меньше лимита.
        """

        enrollments_count = func.count(CourseEnrollment.enrollment_id)

        result = await self.db.execute(
            select(
                Course.course_id,
                Course.title,
                enrollments_count.label("enrollments_count"),
            )
            .outerjoin(CourseEnrollment, CourseEnrollment.course_id == Course.course_id)
            .group_by(Course.course_id, Course.title)
            .order_by(enrollments_count.desc(), Course.course_id.asc())
            .limit(top_courses)
        )

        return [
            DashboardTopCourse(
                course_id=course_id,
                title=title,
                enrollments_count=count,
            )
            for course_id, title, count in result.all()
        ]

    async def get_users(
            self,
            page: int | None = 1,
            per_page: int | None = 10,
    ) -> AdminQuantityUsers:
        """ПОСТРАНИЧНЫЙ СПИСОК ПОЛЬЗОВАТЕЛЕЙ"""

        pagination = get_pagination(
            page=page,
            page_size=per_page,
        )

        # Total users
        total_result = await self.db.execute(
            select(func.count(User.user_id))
        )

        total = total_result.scalar_one()

        active_sessions_count = (
            select(func.count(UserSession.id))
            .where(
                UserSession.user_id == User.user_id,
                *is_active_session(),
            )
            .correlate(User)
            .scalar_subquery()
        )

        enrollments_count = (
            select(func.count(CourseEnrollment.enrollment_id))
            .where(CourseEnrollment.user_id == User.user_id)
            .correlate(User)
            .scalar_subquery()
        )

        result = await self.db.execute(
            select(
                User.user_id,
                User.name,
                User.email,
                User.phone,
                User.img,
                User.is_default_img,
                User.is_admin,
                User.is_blocked,
                User.created_at,
                active_sessions_count.label("active_sessions"),
                enrollments_count.label("enrollments"),
            )
            .order_by(User.created_at.desc(), User.user_id.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        rows = result.all()

        img_urls = await asyncio.gather(*(
            get_avatar_url(img=row.img, is_default_img=bool(row.is_default_img))
            for row in rows
        ))

        users = [
            AdminUserItem(
                user_id=row.user_id,
                name=row.name,
                email=row.email,
                phone=row.phone,
                img_url=img_url,
                is_admin=bool(row.is_admin),
                is_blocked=bool(row.is_blocked),
                created_at=row.created_at,
                active_sessions=row.active_sessions,
                enrollments=row.enrollments,
            )
            for row, img_url in zip(rows, img_urls)
        ]

        return AdminQuantityUsers(
            users=users,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=get_total_pages(
                total=total,
                page_size=pagination.page_size,
            ),
        )

    async def get_user_detail(
            self,
            request: Request,
            user_id: int,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            admin_id: int | None = None,
            platform: str | None = None,
    ) -> AdminUserDetail:
        """ПОДРОБНАЯ КАРТОЧКА ПОЛЬЗОВАТЕЛЯ

        Регистрация, способы входа, согласия, сессии с ip/страной/прокси,
        курсы с прогрессом и последние попытки решения уроков.
        """

        result = await self.db.execute(
            select(User)
            .where(User.user_id == user_id)
        )

        user = result.scalar_one_or_none()

        if user is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="USER_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=admin_id,
                platform=platform,
            )

        img_url = await get_avatar_url(
            img=user.img,
            is_default_img=bool(user.is_default_img),
        )

        sessions = await self._get_sessions(user_id=user_id)
        auth_methods = await self._get_auth_methods(user_id=user_id)
        consents = await self._get_consents(user_id=user_id)

        learning, courses = await self._get_learning(user_id=user_id)
        recent_attempts = await self._get_recent_attempts(user_id=user_id)

        active_sessions = len([
            session for session in sessions
            if session.is_active
        ])

        return AdminUserDetail(
            user=AdminUserItem(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                img_url=img_url,
                is_admin=bool(user.is_admin),
                is_blocked=bool(user.is_blocked),
                created_at=user.created_at,
                active_sessions=active_sessions,
                enrollments=learning.enrollments,
            ),
            total_sessions=len(sessions),
            active_sessions=active_sessions,
            learning=learning,
            auth_methods=auth_methods,
            consents=consents,
            sessions=sessions,
            courses=courses,
            recent_attempts=recent_attempts,
        )

    # ---------- внутренние методы ----------

    async def _get_auth_methods(self, user_id: int) -> list[AdminUserAuthMethod]:
        """СПОСОБЫ ВХОДА ПОЛЬЗОВАТЕЛЯ

        password_hash наружу не отдаём: админке достаточно,
        какими провайдерами человек заходил.
        """

        result = await self.db.execute(
            select(UserAuthMethod, Provider.name)
            .join(Provider, Provider.code == UserAuthMethod.provider)
            .where(UserAuthMethod.user_id == user_id)
            .order_by(UserAuthMethod.created_at)
        )

        return [
            AdminUserAuthMethod(
                provider=method.provider,
                provider_name=provider_name,
                provider_user_id=method.provider_user_id,
                created_at=method.created_at,
            )
            for method, provider_name in result.all()
        ]

    async def _get_consents(self, user_id: int) -> list[AdminUserConsent]:
        """СОГЛАСИЯ НА ОБРАБОТКУ ПЕРСОНАЛЬНЫХ ДАННЫХ"""

        result = await self.db.execute(
            select(UserConsent)
            .where(UserConsent.user_id == user_id)
            .order_by(UserConsent.accepted_at.desc())
        )

        return [
            AdminUserConsent(
                consent_code=consent.consent_code,
                is_accepted=consent.is_accepted,
                policy_version=consent.policy_version,
                ip=as_ip(consent.ip),
                accepted_at=consent.accepted_at,
            )
            for consent in result.scalars().all()
        ]

    async def _get_sessions(self, user_id: int) -> list[AdminUserSession]:
        """СЕССИИ ПОЛЬЗОВАТЕЛЯ

        Страна и прокси в самой сессии не хранятся — они пишутся
        в лог запросов, поэтому берём последнее событие каждой сессии.
        """

        result = await self.db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )

        sessions = result.scalars().all()

        if not sessions:
            return []

        # DISTINCT ON оставляет по одной строке на сессию — последнюю
        logs_result = await self.db.execute(
            select(
                UserEventLog.session_id,
                UserEventLog.ip_address,
                UserEventLog.country_code,
                UserEventLog.is_proxy,
                UserEventLog.created_at,
            )
            .where(UserEventLog.session_id.in_([session.id for session in sessions]))
            .distinct(UserEventLog.session_id)
            .order_by(UserEventLog.session_id, UserEventLog.created_at.desc())
        )

        logs = {row.session_id: row for row in logs_result.all()}

        now = datetime.now(timezone.utc)

        session_items = []

        for session in sessions:
            log = logs.get(session.id)

            session_items.append(
                AdminUserSession(
                    session_id=session.id,
                    provider=session.provider,
                    platform=session.platform,
                    device_name=session.device_name,
                    device_id=session.device_id,
                    language=session.language,
                    ip=as_ip(log.ip_address if log else session.ip),
                    country_code=log.country_code if log else None,
                    is_proxy=log.is_proxy if log else None,
                    created_at=session.created_at,
                    expires_at=session.expires_at,
                    revoked_at=session.revoked_at,
                    last_seen_at=log.created_at if log else None,
                    is_active=session.revoked_at is None and session.expires_at > now,
                )
            )

        return session_items

    async def _get_learning(
            self,
            user_id: int,
    ) -> tuple[AdminUserLearningStats, list[AdminUserCourseProgress]]:
        """КУРСЫ ПОЛЬЗОВАТЕЛЯ И ПРОГРЕСС ПО УРОКАМ"""

        # сколько уроков в курсе — считаем только опубликованные
        lessons_total = (
            select(func.count(Lesson.lesson_id))
            .select_from(Lesson)
            .join(CourseModule, CourseModule.module_id == Lesson.module_id)
            .where(
                CourseModule.course_id == Course.course_id,
                CourseModule.is_published.is_(True),
                Lesson.is_published.is_(True),
            )
            .correlate(Course)
            .scalar_subquery()
        )

        courses_result = await self.db.execute(
            select(
                Course.course_id,
                Course.slug,
                Course.title,
                Course.is_published,
                CourseEnrollment.created_at,
                lessons_total.label("lessons_total"),
            )
            .join(CourseEnrollment, CourseEnrollment.course_id == Course.course_id)
            .where(CourseEnrollment.user_id == user_id)
            .order_by(CourseEnrollment.created_at.desc())
        )

        courses = courses_result.all()

        if not courses:
            return AdminUserLearningStats(), []

        # попытки пользователя по каждому курсу
        attempts_result = await self.db.execute(
            select(
                CourseModule.course_id,
                func.count(LessonAttempt.attempt_id).label("attempts"),
                func.count(distinct(LessonAttempt.lesson_id)).label("lessons_with_attempts"),
            )
            .select_from(LessonAttempt)
            .join(Lesson, Lesson.lesson_id == LessonAttempt.lesson_id)
            .join(CourseModule, CourseModule.module_id == Lesson.module_id)
            .where(LessonAttempt.user_id == user_id)
            .group_by(CourseModule.course_id)
        )

        attempts = {row.course_id: row for row in attempts_result.all()}

        # решённые уроки: есть хотя бы одна попытка с максимальной оценкой
        solved_result = await self.db.execute(
            select(
                CourseModule.course_id,
                func.count(distinct(LessonAttempt.lesson_id)),
            )
            .select_from(LessonAttempt)
            .join(Lesson, Lesson.lesson_id == LessonAttempt.lesson_id)
            .join(CourseModule, CourseModule.module_id == Lesson.module_id)
            .where(
                LessonAttempt.user_id == user_id,
                LessonAttempt.correctness == SOLVED_CORRECTNESS,
            )
            .group_by(CourseModule.course_id)
        )

        solved = {row.course_id: row[1] for row in solved_result.all()}

        course_items = []

        for course in courses:
            attempt = attempts.get(course.course_id)

            course_items.append(
                AdminUserCourseProgress(
                    course_id=course.course_id,
                    slug=course.slug,
                    title=course.title,
                    is_published=bool(course.is_published),
                    enrolled_at=course.created_at,
                    lessons_total=course.lessons_total,
                    lessons_with_attempts=attempt.lessons_with_attempts if attempt else 0,
                    lessons_solved=solved.get(course.course_id, 0),
                    attempts_total=attempt.attempts if attempt else 0,
                )
            )

        last_attempt_result = await self.db.execute(
            select(func.max(LessonAttempt.created_at))
            .where(LessonAttempt.user_id == user_id)
        )

        learning = AdminUserLearningStats(
            enrollments=len(course_items),
            lessons_with_attempts=sum(item.lessons_with_attempts for item in course_items),
            lessons_solved=sum(item.lessons_solved for item in course_items),
            attempts_total=sum(item.attempts_total for item in course_items),
            last_attempt_at=last_attempt_result.scalar_one_or_none(),
        )

        return learning, course_items

    async def _get_recent_attempts(self, user_id: int) -> list[AdminUserLessonAttempt]:
        """ПОСЛЕДНИЕ ПОПЫТКИ РЕШЕНИЯ УРОКОВ"""

        result = await self.db.execute(
            select(
                LessonAttempt.attempt_id,
                LessonAttempt.lesson_id,
                Lesson.title,
                LessonAttempt.code,
                LessonAttempt.correctness,
                LessonAttempt.speed,
                LessonAttempt.created_at,
            )
            .join(Lesson, Lesson.lesson_id == LessonAttempt.lesson_id)
            .where(LessonAttempt.user_id == user_id)
            .order_by(LessonAttempt.created_at.desc())
            .limit(RECENT_ATTEMPTS_LIMIT)
        )

        return [
            AdminUserLessonAttempt(
                attempt_id=row.attempt_id,
                lesson_id=row.lesson_id,
                lesson_title=row.title,
                code=row.code,
                correctness=row.correctness,
                speed=row.speed,
                created_at=row.created_at,
            )
            for row in result.all()
        ]
