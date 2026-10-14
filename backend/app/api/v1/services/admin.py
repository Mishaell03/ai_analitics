import asyncio
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin import (
    DashboardLatestUser,
    DashboardResponse,
    DashboardTopCourse,
)
from app.core.avatars import get_avatar_url
from app.models.auth import UserSession
from app.models.courses import Course, Lesson
from app.models.enrollments_progress import CourseEnrollment
from app.models.users import User


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
