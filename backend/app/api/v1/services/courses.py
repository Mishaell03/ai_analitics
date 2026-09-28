from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import raise_backend_error

from app.api.v1.schemas.courses import (
    CourseDetailResponse,
    CourseItem,
    CoursesResponse,
    ModuleItem,
    CourseInfo,
    LessonDetailResponse,
    CourseShortInfo,
    ModuleShortInfo,
    LessonInfo,
    LessonsResponse,
    ModuleInfo,
    LessonItem,
    EnrollmentResponse
)
from app.core.config import settings
from app.core.minio_url import minio_storage
from app.models.courses import Course, CourseModule, Lesson
from app.core.pagination import get_pagination, get_total_pages
from app.models.enrollments_progress import CourseEnrollment


class BaseCoursesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_courses(
            self,
            page: int = 1,
            page_size: int = 10,
            user_id: int | None = None,
    ) -> CoursesResponse:
        """MINIMAL INFORMATION OF THE COURSES"""

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

        enrolled_ids = set()

        if user_id is not None and courses:
            enrolled_result = await self.db.execute(
                select(CourseEnrollment.course_id)
                .where(
                    CourseEnrollment.user_id == user_id,
                    CourseEnrollment.course_id.in_([course.course_id for course in courses]),
                )
            )

            enrolled_ids = set(enrolled_result.scalars().all())

        course_items = []

        for course in courses:
            image_path = f"{course.course_id}/main.webp"

            main_image_url = await minio_storage.get_url(
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
                    is_enrolled=course.course_id in enrolled_ids,
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
            request: Request,
            course_slug: str,
            language: str,
            page: int = 1,
            page_size: int = 20,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> CourseDetailResponse:
        """DETAIL INFORMATION OF THE COURSE"""

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.slug == course_slug,
                Course.is_published.is_(True),
            )
        )

        course = course_result.scalar_one_or_none()

        if course is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Is the user enrolled
        is_enrolled = False

        if user_id is not None:
            enrolled_result = await self.db.execute(
                select(CourseEnrollment.enrollment_id)
                .where(
                    CourseEnrollment.user_id == user_id,
                    CourseEnrollment.course_id == course.course_id,
                )
            )

            is_enrolled = enrolled_result.scalar_one_or_none() is not None

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
            module_content_url = None

            if is_enrolled:
                module_content_url = await minio_storage.get_url(
                    file_path=f"{module.module_id}/content.md",
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
            main_image_url = await minio_storage.get_url(
                file_path=f"{course.course_id}/main.webp",
                expires=settings.image_url_ttl,
                bucket="course-content",
            )

            content_url = await minio_storage.get_url(
                file_path=f"{course.course_id}/content.md",
                expires=settings.content_url_ttl,
                bucket="course-content",
            )

            course_info = CourseInfo(
                slug=course.slug,
                title=course.title,
                description=course.description,
                main_image_url=main_image_url,
                content_url=content_url,
                is_enrolled=is_enrolled,
            )

        return CourseDetailResponse(
            course=course_info,
            modules=module_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_lessons(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            language: str,
            page: int = 1,
            page_size: int = 20,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> LessonsResponse:
        """LIST OF LESSONS OF THE SELECTED MODULE"""

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.slug == course_slug,
                Course.is_published.is_(True),
            )
        )
        course = course_result.scalar_one_or_none()

        if course is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Module
        module_result = await self.db.execute(
            select(CourseModule)
            .where(
                CourseModule.module_id == module_id,
                CourseModule.course_id == course.course_id,
            )
        )
        module = module_result.scalar_one_or_none()

        if module is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="MODULE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Is the user enrolled
        is_enrolled = False

        if user_id is not None:
            enrolled_result = await self.db.execute(
                select(CourseEnrollment.enrollment_id)
                .where(
                    CourseEnrollment.user_id == user_id,
                    CourseEnrollment.course_id == course.course_id,
                )
            )
            is_enrolled = enrolled_result.scalar_one_or_none() is not None

        # Total lessons
        total_result = await self.db.execute(
            select(func.count(Lesson.lesson_id))
            .where(
                Lesson.module_id == module.module_id,
            )
        )
        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        lessons_result = await self.db.execute(
            select(Lesson)
            .where(
                Lesson.module_id == module.module_id,
            )
            .order_by(Lesson.position)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        lessons = lessons_result.scalars().all()

        lesson_items = [
            LessonItem(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                description=lesson.description,
                position=lesson.position,
            )
            for lesson in lessons
        ]

        # Module information only on the first page
        module_info = None

        if pagination.page == 1:
            module_content_url = None

            # Module content only for enrolled users
            if is_enrolled:
                module_content_url = await minio_storage.get_url(
                    file_path=f"{module.module_id}/content.md",
                    expires=settings.content_url_ttl,
                    bucket="module-content",
                )

            module_info = ModuleInfo(
                module_id=module.module_id,
                title=module.title,
                description=module.description,
                position=module.position,
                content_url=module_content_url,
            )

        return LessonsResponse(
            module=module_info,
            lessons=lesson_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_lesson(
            self,
            request: Request,
            course_slug: str,
            module_id: int,
            lesson_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> LessonDetailResponse:
        """DETAIL INFORMATION OF THE LESSON"""

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.slug == course_slug,
                Course.is_published.is_(True),
            )
        )
        course = course_result.scalar_one_or_none()

        if course is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Module
        module_result = await self.db.execute(
            select(CourseModule)
            .where(
                CourseModule.module_id == module_id,
                CourseModule.course_id == course.course_id,
            )
        )
        module = module_result.scalar_one_or_none()

        if module is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="MODULE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Lesson
        lesson_result = await self.db.execute(
            select(Lesson)
            .where(
                Lesson.lesson_id == lesson_id,
                Lesson.module_id == module.module_id,
            )
        )
        lesson = lesson_result.scalar_one_or_none()

        if lesson is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="LESSON_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Is the user enrolled
        is_enrolled = False

        if user_id is not None:
            enrolled_result = await self.db.execute(
                select(CourseEnrollment.enrollment_id)
                .where(
                    CourseEnrollment.user_id == user_id,
                    CourseEnrollment.course_id == course.course_id,
                )
            )

            is_enrolled = enrolled_result.scalar_one_or_none() is not None

        # Lesson content only for enrolled users
        content_url = None

        if is_enrolled:
            content_url = await minio_storage.get_url(
                file_path=f"{lesson.lesson_id}/content.md",
                expires=settings.content_url_ttl,
                bucket="lesson-content",
            )

        return LessonDetailResponse(
            course=CourseShortInfo(
                course_id=course.course_id,
                slug=course.slug,
                title=course.title,
            ),
            module=ModuleShortInfo(
                module_id=module.module_id,
                title=module.title,
                position=module.position,
            ),
            lesson=LessonInfo(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                description=lesson.description,
                position=lesson.position,
                content_url=content_url,
            ),
        )

    async def enroll_course(
            self,
            request: Request,
            course_slug: str,
            user_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            platform: str | None = None,
    ) -> EnrollmentResponse:
        """ENROLL THE USER IN THE COURSE"""

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.slug == course_slug,
                Course.is_published.is_(True),
            )
        )
        course = course_result.scalar_one_or_none()

        if course is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Is the user already enrolled
        enrolled_result = await self.db.execute(
            select(CourseEnrollment.enrollment_id)
            .where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course.course_id,
            )
        )

        if enrolled_result.scalar_one_or_none() is not None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_ALREADY_ENROLLED",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Enrollment
        self.db.add(
            CourseEnrollment(
                user_id=user_id,
                course_id=course.course_id,
            )
        )

        try:
            await self.db.commit()
        except IntegrityError:
            # Two requests at the same time: UNIQUE(user_id, course_id) fired
            await self.db.rollback()

            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_ALREADY_ENROLLED",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        return EnrollmentResponse (
            success=True,
        )

    async def unenroll_course(
            self,
            request: Request,
            course_slug: str,
            user_id: int,
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            platform: str | None = None,
    ) -> EnrollmentResponse:
        """UNENROLL THE USER FROM THE COURSE"""

        # Course
        course_result = await self.db.execute(
            select(Course)
            .where(
                Course.slug == course_slug,
                Course.is_published.is_(True),
            )
        )
        course = course_result.scalar_one_or_none()

        if course is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_FOUND",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        # Enrollment
        enrollment_result = await self.db.execute(
            select(CourseEnrollment)
            .where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course.course_id,
            )
        )
        enrollment = enrollment_result.scalar_one_or_none()

        if enrollment is None:
            await raise_backend_error(
                db=self.db,
                request=request,
                code="COURSE_NOT_ENROLLED",
                language=language,
                device_id=device_id,
                session_id=session_id,
                user_id=user_id,
                platform=platform,
            )

        await self.db.delete(enrollment)
        await self.db.commit()

        return EnrollmentResponse(
            success=True,
        )