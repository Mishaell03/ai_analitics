from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import (
    CourseDetailResponse,
    CourseItem,
    CoursesResponse,
    ModuleItem,
    CourseInfo
)
from app.core.config import settings
from app.core.minio_url import get_minio_url
from app.models.courses import Course, CourseModule
from app.core.pagination import get_pagination, get_total_pages


class BaseCoursesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_courses(
            self,
            page: int = 1,
            page_size: int = 10,
    ) -> CoursesResponse:

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        # Total courses
        total_result = await self.db.execute(
            select(func.count(Course.course_id))
            .where(Course.is_published.is_(True))
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        result = await self.db.execute(
            select(Course)
            .where(Course.is_published.is_(True))
            .order_by(Course.course_id)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        courses = result.scalars().all()

        course_items = []

        for course in courses:
            image_path = f"{course.course_id}/main.webp"

            main_image_url = await get_minio_url(
                file_path=image_path,
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
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_course(
            self,
            course_id: int,
            page: int = 1,
            page_size: int = 20,
    ) -> CourseDetailResponse | None:

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.course_id == course_id,
                Course.is_published.is_(True),
            )
        )

        course = course_result.scalar_one_or_none()

        if course is None:
            return None

        # Total modules
        total_result = await self.db.execute(
            select(func.count(CourseModule.module_id))
            .where(
                CourseModule.course_id == course.course_id,
            )
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        modules_result = await self.db.execute(
            select(CourseModule)
            .where(
                CourseModule.course_id == course.course_id,
            )
            .order_by(CourseModule.position)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        modules = modules_result.scalars().all()

        module_items = []

        for module in modules:
            module_content_path = f"{module.module_id}/content.md"

            module_content_url = await get_minio_url(
                file_path=module_content_path,
                expires=settings.content_url_ttl,
                bucket="module-content",
            )

            module_items.append(
                ModuleItem(
                    module_id=module.module_id,
                    title=module.title,
                    description=module.description,
                    position=module.position,
                    content_url=module_content_url,
                )
            )

        # Course information only on the first page
        course_info = None

        if pagination.page == 1:
            image_path = f"{course.course_id}/main.webp"

            main_image_url = await get_minio_url(
                file_path=image_path,
                expires=settings.image_url_ttl,
                bucket="course-content",
            )

            content_path = f"{course.course_id}/content.md"

            content_url = await get_minio_url(
                file_path=content_path,
                expires=settings.content_url_ttl,
                bucket="course-content",
            )

            course_info = CourseInfo(
                course_id=course.course_id,
                slug=course.slug,
                title=course.title,
                description=course.description,
                main_image_url=main_image_url,
                content_url=content_url,
            )

        return CourseDetailResponse(
            course=course_info,
            modules=module_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )
