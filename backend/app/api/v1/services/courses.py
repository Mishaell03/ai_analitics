from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import CoursesResponse, CourseItem
from app.models.courses import Course
from app.core.config import settings
from app.core.minio_url import get_minio_url


class BaseCoursesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_courses(
        self,
        page: int = 1,
        page_size: int = 10,
    ) -> CoursesResponse:

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 10

        # Total courses
        total_result = await self.db.execute(
            select(func.count(Course.course_id))
            .where(Course.is_published.is_(True))
        )

        total = total_result.scalar_one()

        total_pages = (
            (total + page_size - 1) # page_size
            if total > 0
            else 0
        )

        # Courses
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(Course)
            .where(Course.is_published.is_(True))
            .order_by(Course.course_id)
            .offset(offset)
            .limit(page_size)
        )

        courses = result.scalars().all()

        course_items = []

        for course in courses:
            main_image_url = None

            if course.content_path:
                main_image_url = get_minio_url(
                    file_path=course.content_path,
                    expires=settings.image_url_ttl,
                    bucket="course-content",
                )

            course_items.append(
                CourseItem(
                    slug=course.slug,
                    title=course.title,
                    description=course.description,
                    main_image_url=main_image_url,
                )
            )

        return CoursesResponse(
            courses=course_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )
