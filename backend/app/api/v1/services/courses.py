from typing import Any, NoReturn

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import raise_backend_error

from app.api.v1.schemas.courses import (
    CourseDetailResponse,
    CourseInfo,
    CourseItem,
    CourseShortInfo,
    CoursesResponse,
    EnrollmentResponse,
    LessonDetailResponse,
    LessonInfo,
    LessonItem,
    LessonReorderRequest,
    LessonsAdminResponse,
    LessonsResponse,
    ModuleInfo,
    ModuleItem,
    ModuleReorderRequest,
    ModuleShortInfo
)
from app.core.config import settings
from app.core.minio_url import minio_storage
from app.core.storage_paths import (
    COURSE_CONTENT_BUCKET,
    course_content_path,
    course_cover_object_key,
    course_prefix,
    lesson_content_path,
    module_content_path,
    module_prefix,
)
from app.models.courses import Course, CourseModule, Lesson
from app.core.pagination import get_pagination, get_total_pages
from app.models.enrollments_progress import CourseEnrollment


def is_published(model):
    """УСЛОВИЕ «СУЩНОСТЬ ОПУБЛИКОВАНА»

    Черновики не показываем ни в списках, ни в содержимом.
    """

    return model.is_published.is_(True)


class BaseCoursesService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- служебное ----------

    @staticmethod
    def _error(
            language: str,
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> dict:
        """Параметры логирования ошибки для raise_backend_error."""

        return dict(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

    async def _raise(
            self,
            request: Request,
            code: str,
            error: dict,
    ) -> NoReturn:
        await raise_backend_error(
            db=self.db,
            request=request,
            code=code,
            **error,
        )

    # ---------- доступ к сущностям ----------

    async def _get_course(
            self,
            request: Request,
            course_slug: str,
            error: dict,
    ) -> Course:
        """КУРС ПО SLUG

        Неопубликованный курс — ошибка, а не пустой ответ:
        так клиент не видит черновик и не путает его с отсутствующим.
        """

        result = await self.db.execute(
            select(Course)
            .where(Course.slug == course_slug)
        )

        course = result.scalar_one_or_none()

        if course is None:
            await self._raise(
                request=request,
                code="COURSE_NOT_FOUND",
                error=error,
            )

        if not course.is_published:
            await self._raise(
                request=request,
                code="COURSE_NOT_PUBLISHED",
                error=error,
            )

        return course

    async def _get_module(
            self,
            request: Request,
            course: Course,
            module_id: int,
            error: dict,
    ) -> CourseModule:
        """МОДУЛЬ КУРСА

        Модуль ищется только внутри своего курса, чтобы нельзя было
        открыть модуль чужого курса по прямой ссылке.
        """

        result = await self.db.execute(
            select(CourseModule)
            .where(
                CourseModule.module_id == module_id,
                CourseModule.course_id == course.course_id,
            )
        )

        module = result.scalar_one_or_none()

        if module is None:
            await self._raise(
                request=request,
                code="MODULE_NOT_FOUND",
                error=error,
            )

        if not module.is_published:
            await self._raise(
                request=request,
                code="MODULE_NOT_PUBLISHED",
                error=error,
            )

        return module

    async def _get_lesson(
            self,
            request: Request,
            module: CourseModule,
            lesson_id: int,
            error: dict,
    ) -> Lesson:
        """УРОК МОДУЛЯ

        Урок ищется только внутри своего модуля — по той же причине,
        что и модуль внутри курса.
        """

        result = await self.db.execute(
            select(Lesson)
            .where(
                Lesson.lesson_id == lesson_id,
                Lesson.module_id == module.module_id,
            )
        )

        lesson = result.scalar_one_or_none()

        if lesson is None:
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        if not lesson.is_published:
            await self._raise(
                request=request,
                code="LESSON_NOT_PUBLISHED",
                error=error,
            )

        return lesson

    async def _get_cover_urls(self, course_ids: list[int]) -> dict[int, str | None]:
        """ССЫЛКИ НА ОБЛОЖКИ КУРСОВ

        Обложка всегда лежит по фиксированному пути
        `{course_id}/main.webp`; запись в БД нужна только для метаданных.
        """

        from app.models.media import CourseImage

        covers: dict[int, CourseImage] = {}

        if course_ids:
            result = await self.db.execute(
                select(CourseImage).where(CourseImage.course_id.in_(course_ids))
            )

            covers = {image.course_id: image for image in result.scalars().all()}

        urls: dict[int, str | None] = {}

        for course_id in course_ids:
            object_key = course_cover_object_key(course_id=course_id)

            if object_key is None:
                urls[course_id] = None

                continue

            expires = (
                settings.media_url_ttl
                if covers.get(course_id) is not None
                else settings.image_url_ttl
            )

            urls[course_id] = await minio_storage.get_url(
                file_path=object_key,
                expires=expires,
                bucket=COURSE_CONTENT_BUCKET,
            )

        return urls

    async def _get_cover_url(self, course_id: int) -> str | None:
        """ССЫЛКА НА ОБЛОЖКУ ОДНОГО КУРСА"""

        object_key = course_cover_object_key(course_id=course_id)

        if object_key is None:
            return None

        return await minio_storage.get_url(
            file_path=object_key,
            expires=settings.image_url_ttl,
            bucket=COURSE_CONTENT_BUCKET,
        )

    async def _is_enrolled(self, user_id: int | None, course_id: int) -> bool:
        """ЗАПИСАН ЛИ ПОЛЬЗОВАТЕЛЬ НА КУРС"""

        if user_id is None:
            return False

        result = await self.db.execute(
            select(CourseEnrollment.enrollment_id)
            .where(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id,
            )
        )

        return result.scalar_one_or_none() is not None

    # ---------- публичное API ----------

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
            .where(is_published(Course))
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        result = await self.db.execute(
            select(Course)
            .where(is_published(Course))
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

        cover_urls = await self._get_cover_urls(
            course_ids=[course.course_id for course in courses],
        )

        for course in courses:
            course_items.append(
                CourseItem(
                    slug=course.slug,
                    title=course.title,
                    description=course.description,
                    main_image_url=cover_urls.get(course.course_id),
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

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        # Is the user enrolled
        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        # Total modules: только опубликованные, иначе поедут страницы
        total_result = await self.db.execute(
            select(func.count(CourseModule.module_id))
            .where(
                CourseModule.course_id == course.course_id,
                is_published(CourseModule),
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
                is_published(CourseModule),
            )
            .order_by(CourseModule.position)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        modules = modules_result.scalars().all()

        module_items = []

        for module in modules:
            module_content_url = None

            file_path = module_content_path(
                course_id=course.course_id,
                module_id=module.module_id,
            )

            if is_enrolled and file_path is not None:
                module_content_url = await minio_storage.get_url(
                    file_path=file_path,
                    expires=settings.content_url_ttl,
                    bucket=COURSE_CONTENT_BUCKET,
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
            cover_urls = await self._get_cover_urls(
                course_ids=[course.course_id],
            )

            main_image_url = cover_urls.get(course.course_id)

            file_path = course_content_path(course_id=course.course_id)

            content_url = None

            if file_path is not None:
                content_url = await minio_storage.get_url(
                    file_path=file_path,
                    expires=settings.content_url_ttl,
                    bucket=COURSE_CONTENT_BUCKET,
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

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        module = await self._get_module(
            request=request,
            course=course,
            module_id=module_id,
            error=error,
        )

        # Is the user enrolled
        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        # Total lessons: только опубликованные, иначе поедут страницы
        total_result = await self.db.execute(
            select(func.count(Lesson.lesson_id))
            .where(
                Lesson.module_id == module.module_id,
                is_published(Lesson),
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
                is_published(Lesson),
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

            file_path = module_content_path(
                course_id=course.course_id,
                module_id=module.module_id,
            )

            # Module content only for enrolled users
            if is_enrolled and file_path is not None:
                module_content_url = await minio_storage.get_url(
                    file_path=file_path,
                    expires=settings.content_url_ttl,
                    bucket=COURSE_CONTENT_BUCKET,
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

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        module = await self._get_module(
            request=request,
            course=course,
            module_id=module_id,
            error=error,
        )

        lesson = await self._get_lesson(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        # Is the user enrolled
        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        # Lesson content only for enrolled users
        content_url = None

        lesson_file_path = lesson_content_path(
            course_id=course.course_id,
            module_id=module.module_id,
            lesson_id=lesson.lesson_id,
        )

        if is_enrolled and lesson_file_path is not None:
            content_url = await minio_storage.get_url(
                file_path=lesson_file_path,
                expires=settings.content_url_ttl,
                bucket=COURSE_CONTENT_BUCKET,
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

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        # Is the user already enrolled
        is_enrolled = await self._is_enrolled(
            user_id=user_id,
            course_id=course.course_id,
        )

        if is_enrolled:
            await self._raise(
                request=request,
                code="COURSE_ALREADY_ENROLLED",
                error=error,
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

            await self._raise(
                request=request,
                code="COURSE_ALREADY_ENROLLED",
                error=error,
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

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course(
            request=request,
            course_slug=course_slug,
            error=error,
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
            await self._raise(
                request=request,
                code="COURSE_NOT_ENROLLED",
                error=error,
            )

        await self.db.delete(enrollment)
        await self.db.commit()



        return EnrollmentResponse(
            success=True,
        )

    # ---------- ADMIN: COURSES ----------

    async def get_courses_admin(
            self,
            page: int = 1,
            page_size: int = 20,
    ):
        from app.api.v1.schemas.courses import CoursesAdminResponse, CourseAdminItem

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        total_result = await self.db.execute(
            select(func.count(Course.course_id))
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        # сколько модулей и уроков внутри курса — админу это нужно
        # сразу, без дополнительных запросов по каждому курсу
        modules_count = (
            select(func.count(CourseModule.module_id))
            .where(CourseModule.course_id == Course.course_id)
            .correlate(Course)
            .scalar_subquery()
        )

        lessons_count = (
            select(func.count(Lesson.lesson_id))
            .join(CourseModule, CourseModule.module_id == Lesson.module_id)
            .where(CourseModule.course_id == Course.course_id)
            .correlate(Course)
            .scalar_subquery()
        )

        result = await self.db.execute(
            select(Course, modules_count, lessons_count)
            .order_by(Course.course_id)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        courses = result.all()

        course_items = []

        # обложки курсов: сначала загруженная, иначе старый файл
        cover_urls = await self._get_cover_urls(
            course_ids=[course.course_id for course, _, _ in courses],
        )

        for course, course_modules_count, course_lessons_count in courses:
            course_items.append(
                CourseAdminItem(
                    slug=course.slug,
                    title=course.title,
                    description=course.description,
                    main_image_url=cover_urls.get(course.course_id),
                    is_enrolled=False,
                    is_active=course.is_published,
                    modules_count=course_modules_count,
                    lessons_count=course_lessons_count,
                )
            )

        return CoursesAdminResponse(
            courses=course_items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def create_course(
            self,
            request: Request,
            data,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        import uuid
        import re

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        slug = data.slug

        if not slug:
            base = re.sub(r"[^a-z0-9]+", "-", (data.title or "").lower()).strip("-")
            if not base:
                base = "course"
            slug = f"{base}-{uuid.uuid4().hex[:8]}"

        is_published = data.is_published
        if is_published is None:
            is_published = data.is_active if data.is_active is not None else False

        course = Course(
            slug=slug,
            title=data.title,
            description=data.description,
            is_published=is_published,
        )

        self.db.add(course)

        try:
            await self.db.commit()
            await self.db.refresh(course)
        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="REGISTRATION_FAILED",
                error=error,
            )

        main_image_url = await self._get_cover_url(course_id=course.course_id)

        from app.api.v1.schemas.courses import CourseAdminResponse

        return CourseAdminResponse(
            slug=course.slug,
            title=course.title,
            description=course.description,
            main_image_url=main_image_url,
            is_enrolled=False,
            is_active=course.is_published,
            success=True,
            course_id=course.course_id,
            id=course.course_id,
            is_published=course.is_published,
        )

    async def _get_course_admin(
            self,
            request: Request,
            course_slug: str,
            error: dict,
    ) -> Course:
        if str(course_slug).isdigit():
            condition = Course.course_id == int(course_slug)
        else:
            condition = Course.slug == course_slug

        result = await self.db.execute(
            select(Course).where(condition)
        )

        course = result.scalar_one_or_none()

        if course is None:
            await self._raise(
                request=request,
                code="COURSE_NOT_FOUND",
                error=error,
            )

        return course

    async def update_course(
            self,
            request: Request,
            course_slug: str,
            data,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        from app.api.v1.schemas.courses import CourseAdminResponse

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] is not None:
            course.slug = update_data["slug"]

        if "title" in update_data and update_data["title"] is not None:
            course.title = update_data["title"]

        if "description" in update_data:
            course.description = update_data["description"]

        if "is_published" in update_data and update_data["is_published"] is not None:
            course.is_published = update_data["is_published"]

        if "is_active" in update_data and update_data["is_active"] is not None:
            course.is_published = update_data["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(course)
        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        main_image_url = await self._get_cover_url(course_id=course.course_id)

        return CourseAdminResponse(
            slug=course.slug,
            title=course.title,
            description=course.description,
            main_image_url=main_image_url,
            is_enrolled=False,
            is_active=course.is_published,
            success=True,
            course_id=course.course_id,
            id=course.course_id,
            is_published=course.is_published,
        )

    # ---------- ADMIN: COURSES DELETE / DEACTIVATE ----------

    async def delete_course(
            self,
            request: Request,
            course_slug: str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        await self.db.delete(course)
        await self.db.commit()

        # после удаления курса в хранилище не должно остаться его файлов:
        # обложки, текстов уроков, медиа и вводных текстов
        prefix = course_prefix(course_id=course.course_id)

        if prefix is not None:
            await minio_storage.delete_prefix(
                bucket=COURSE_CONTENT_BUCKET,
                prefix=prefix,
            )

        from app.api.v1.schemas.courses import EnrollmentResponse
        return EnrollmentResponse(success=True)

    async def deactivate_course(
            self,
            request: Request,
            course_slug: str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        course.is_published = False
        await self.db.commit()
        await self.db.refresh(course)

        main_image_url = await self._get_cover_url(course_id=course.course_id)

        from app.api.v1.schemas.courses import CourseAdminResponse
        return CourseAdminResponse(
            slug=course.slug,
            title=course.title,
            description=course.description,
            main_image_url=main_image_url,
            is_enrolled=False,
            is_active=False,
            success=True,
            course_id=course.course_id,
            id=course.course_id,
            is_published=False,
        )

    async def activate_course(
            self,
            request: Request,
            course_slug: str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        course.is_published = True
        await self.db.commit()
        await self.db.refresh(course)

        main_image_url = await self._get_cover_url(course_id=course.course_id)

        from app.api.v1.schemas.courses import CourseAdminResponse
        return CourseAdminResponse(
            slug=course.slug,
            title=course.title,
            description=course.description,
            main_image_url=main_image_url,
            is_enrolled=False,
            is_active=True,
            success=True,
            course_id=course.course_id,
            id=course.course_id,
            is_published=True,
        )

    # ---------- ADMIN: MODULES ----------

    async def _resolve_course_for_module(
            self,
            request: Request,
            course_slug: str | None,
            data,
            error: dict,
    ) -> Course:
        ref = course_slug
        if ref is None and data is not None:
            ref = getattr(data, "course_slug", None) or getattr(data, "course_slug", None)
            if ref is None and getattr(data, "course_id", None) is not None:
                ref = str(data.course_id)

        if ref is None:
            await self._raise(
                request=request,
                code="COURSE_NOT_FOUND",
                error=error,
            )

        return await self._get_course_admin(
            request=request,
            course_slug=str(ref),
            error=error,
        )

    async def _get_module_admin(
            self,
            request: Request,
            module_id: int | str,
            error: dict,
    ) -> CourseModule:
        if not str(module_id).isdigit():
            await self._raise(
                request=request,
                code="MODULE_NOT_FOUND",
                error=error,
            )

        result = await self.db.execute(
            select(CourseModule).where(CourseModule.module_id == int(module_id))
        )

        module = result.scalar_one_or_none()

        if module is None:
            await self._raise(
                request=request,
                code="MODULE_NOT_FOUND",
                error=error,
            )

        return module

    async def _get_lesson_admin(
            self,
            request: Request,
            module: CourseModule,
            lesson_id: int | str,
            error: dict,
    ) -> Lesson:
        """УРОК МОДУЛЯ ДЛЯ АДМИНКИ

        Урок ищется только внутри своего модуля и может быть черновиком:
        админ должен видеть всё, что есть в базе.
        """

        if not str(lesson_id).isdigit():
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        result = await self.db.execute(
            select(Lesson).where(
                Lesson.lesson_id == int(lesson_id),
                Lesson.module_id == module.module_id,
            )
        )

        lesson = result.scalar_one_or_none()

        if lesson is None:
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        return lesson

    async def _apply_positions(
            self,
            entities: dict[int, Any],
            ordered_ids: list[int],
    ) -> None:
        """ПЕРЕНАЗНАЧАЕТ ПОЗИЦИИ 1..N

        Позиции ставятся в два шага: сначала временные, потом финальные.
        Иначе уникальный индекс (курс/модуль, позиция) ругается на
        промежуточное состояние — например, при перестановке двух
        модулей местами.
        """

        max_position = max(
            (entity.position for entity in entities.values()),
            default=0,
        )

        for position, entity_id in enumerate(ordered_ids, start=1):
            entities[entity_id].position = max_position + position

        await self.db.flush()

        for position, entity_id in enumerate(ordered_ids, start=1):
            entities[entity_id].position = position

    async def get_modules_admin(
            self,
            course_slug: str,
            request: Request = None,
            page: int = 1,
            page_size: int = 20,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        from app.core.pagination import get_pagination, get_total_pages
        pagination = get_pagination(page=page, page_size=page_size)

        total_result = await self.db.execute(
            select(func.count(CourseModule.module_id)).where(CourseModule.course_id == course.course_id)
        )
        total = total_result.scalar_one()
        total_pages = get_total_pages(total=total, page_size=pagination.page_size)

        result = await self.db.execute(
            select(CourseModule)
            .where(CourseModule.course_id == course.course_id)
            .order_by(CourseModule.position)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        modules = result.scalars().all()

        from app.api.v1.schemas.courses import ModuleAdminResponse, ModulesAdminResponse
        items = [
            ModuleAdminResponse(
                success=True,
                module_id=m.module_id,
                id=m.module_id,
                course_id=m.course_id,
                title=m.title,
                description=m.description,
                position=m.position,
                is_published=m.is_published,
                is_active=m.is_published,
            )
            for m in modules
        ]

        return ModulesAdminResponse(
            modules=items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def create_module(
            self,
            request: Request,
            course_slug: str | None,
            data,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._resolve_course_for_module(
            request=request,
            course_slug=course_slug,
            data=data,
            error=error,
        )

        position = data.position
        if position is None:
            result = await self.db.execute(
                select(func.max(CourseModule.position)).where(CourseModule.course_id == course.course_id)
            )
            max_pos = result.scalar_one_or_none()
            position = (max_pos or 0) + 1

        is_published = data.is_published
        if is_published is None:
            is_published = data.is_active if data.is_active is not None else False

        module = CourseModule(
            course_id=course.course_id,
            title=data.title,
            description=data.description,
            position=position,
            is_published=is_published,
        )

        self.db.add(module)

        try:
            await self.db.commit()
            await self.db.refresh(module)
        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="REGISTRATION_FAILED",
                error=error,
            )

        from app.api.v1.schemas.courses import ModuleAdminResponse
        return ModuleAdminResponse(
            success=True,
            module_id=module.module_id,
            id=module.module_id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            position=module.position,
            is_published=module.is_published,
            is_active=module.is_published,
        )

    async def update_module(
            self,
            request: Request,
            module_id: int | str,
            data,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        update_data = data.model_dump(exclude_unset=True)

        if "course_id" in update_data and update_data["course_id"] is not None:
            module.course_id = update_data["course_id"]
        if "course_slug" in update_data and update_data["course_slug"] is not None:
            # resolve course
            course = await self._get_course_admin(request=request, course_slug=str(update_data["course_slug"]), error=error)
            module.course_id = course.course_id
        if "course_slug" in update_data and update_data["course_slug"] is not None:
            course = await self._get_course_admin(request=request, course_slug=str(update_data["course_slug"]), error=error)
            module.course_id = course.course_id

        if "title" in update_data and update_data["title"] is not None:
            module.title = update_data["title"]

        if "description" in update_data:
            module.description = update_data["description"]

        if "position" in update_data and update_data["position"] is not None:
            module.position = update_data["position"]

        if "is_published" in update_data and update_data["is_published"] is not None:
            module.is_published = update_data["is_published"]

        if "is_active" in update_data and update_data["is_active"] is not None:
            module.is_published = update_data["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(module)
        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        from app.api.v1.schemas.courses import ModuleAdminResponse
        return ModuleAdminResponse(
            success=True,
            module_id=module.module_id,
            id=module.module_id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            position=module.position,
            is_published=module.is_published,
            is_active=module.is_published,
        )

    async def delete_module(
            self,
            request: Request,
            module_id: int | str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        await self.db.delete(module)
        await self.db.commit()

        # файлы модуля: его вводный текст и Markdown всех уроков
        prefix = module_prefix(
            course_id=module.course_id,
            module_id=module.module_id,
        )

        if prefix is not None:
            await minio_storage.delete_prefix(
                bucket=COURSE_CONTENT_BUCKET,
                prefix=prefix,
            )

        from app.api.v1.schemas.courses import EnrollmentResponse
        return EnrollmentResponse(success=True)

    async def deactivate_module(
            self,
            request: Request,
            module_id: int | str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        module.is_published = False
        await self.db.commit()
        await self.db.refresh(module)

        from app.api.v1.schemas.courses import ModuleAdminResponse
        return ModuleAdminResponse(
            success=True,
            module_id=module.module_id,
            id=module.module_id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            position=module.position,
            is_published=False,
            is_active=False,
        )

    async def activate_module(
            self,
            request: Request,
            module_id: int | str,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        module.is_published = True
        await self.db.commit()
        await self.db.refresh(module)

        from app.api.v1.schemas.courses import ModuleAdminResponse
        return ModuleAdminResponse(
            success=True,
            module_id=module.module_id,
            id=module.module_id,
            course_id=module.course_id,
            title=module.title,
            description=module.description,
            position=module.position,
            is_published=True,
            is_active=True,
        )

    async def reorder_modules(
            self,
            request: Request,
            course_slug: str,
            data: ModuleReorderRequest,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        """ПЕРЕСТАНОВКА МОДУЛЕЙ КУРСА

        Принимает список id модулей в новом порядке и переназначает
        position = 1..N. Делается одним транзакцией, чтобы позиции
        не разъехались при сбое на середине.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        result = await self.db.execute(
            select(CourseModule)
            .where(CourseModule.course_id == course.course_id)
        )
        modules = {module.module_id: module for module in result.scalars().all()}

        module_ids = data.module_ids

        # все переданные id должны существовать и принадлежать этому курсу
        if len(module_ids) != len(set(module_ids)) or set(module_ids) != set(modules.keys()):
            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        await self._apply_positions(
            entities=modules,
            ordered_ids=module_ids,
        )

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        from app.api.v1.schemas.courses import ModulesAdminResponse, ModuleAdminResponse
        items = [
            ModuleAdminResponse(
                success=True,
                module_id=module.module_id,
                id=module.module_id,
                course_id=module.course_id,
                title=module.title,
                description=module.description,
                position=module.position,
                is_published=module.is_published,
                is_active=module.is_published,
            )
            for module in sorted(modules.values(), key=lambda m: m.position)
        ]

        return ModulesAdminResponse(
            modules=items,
            total_pages=1,
            current_page=1,
            page_size=len(items),
        )

    # ---------- ADMIN: LESSONS ----------

    async def get_lessons_admin(
            self,
            course_slug: str,
            module_id: int,
            request: Request,
            page: int = 1,
            page_size: int = 20,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        """СПИСОК УРОКОВ МОДУЛЯ ДЛЯ АДМИНКИ

        В отличие от пользовательского списка, админ видит и черновики
        """

        from app.api.v1.schemas.courses import LessonAdminResponse, LessonsAdminResponse

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        course = await self._get_course_admin(
            request=request,
            course_slug=course_slug,
            error=error,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        # модуль должен принадлежать курсу
        if module.course_id != course.course_id:
            await self._raise(
                request=request,
                code="MODULE_NOT_FOUND",
                error=error,
            )

        pagination = get_pagination(
            page=page,
            page_size=page_size,
        )

        total_result = await self.db.execute(
            select(func.count(Lesson.lesson_id))
            .where(Lesson.module_id == module.module_id)
        )

        total = total_result.scalar_one()

        total_pages = get_total_pages(
            total=total,
            page_size=pagination.page_size,
        )

        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.module_id == module.module_id)
            .order_by(Lesson.position)
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        lessons = result.scalars().all()

        items = []

        for lesson in lessons:
            file_path = lesson_content_path(
                course_id=course.course_id,
                module_id=module.module_id,
                lesson_id=lesson.lesson_id,
            )

            # есть ли Markdown урока в хранилище
            has_content = False

            if file_path is not None:
                has_content = await minio_storage.exists(
                    file_path=file_path,
                    bucket=COURSE_CONTENT_BUCKET,
                )

            items.append(
                LessonAdminResponse(
                    success=True,
                    lesson_id=lesson.lesson_id,
                    id=lesson.lesson_id,
                    module_id=lesson.module_id,
                    title=lesson.title,
                    description=lesson.description,
                    position=lesson.position,
                    is_published=lesson.is_published,
                    is_active=lesson.is_published,
                    has_content=has_content,
                )
            )

        return LessonsAdminResponse(
            lessons=items,
            total_pages=total_pages,
            current_page=pagination.page,
            page_size=pagination.page_size,
        )

    async def update_lesson(
            self,
            request: Request,
            module_id: int,
            lesson_id: int,
            data,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ):
        """ПРАВКА МЕТАДАННЫХ УРОКА

        Текст урока лежит в хранилище, поэтому здесь меняются только
        название, описание, позиция и статус публикации.
        """

        from app.api.v1.schemas.courses import LessonAdminResponse

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        lesson = await self._get_lesson_admin(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        update_data = data.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            lesson.title = update_data["title"]

        if "description" in update_data:
            lesson.description = update_data["description"]

        if "position" in update_data and update_data["position"] is not None:
            lesson.position = update_data["position"]

        if "is_published" in update_data and update_data["is_published"] is not None:
            lesson.is_published = update_data["is_published"]

        if "is_active" in update_data and update_data["is_active"] is not None:
            lesson.is_published = update_data["is_active"]

        try:
            await self.db.commit()
            await self.db.refresh(lesson)
        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        return LessonAdminResponse(
            success=True,
            lesson_id=lesson.lesson_id,
            id=lesson.lesson_id,
            module_id=lesson.module_id,
            title=lesson.title,
            description=lesson.description,
            position=lesson.position,
            is_published=lesson.is_published,
            is_active=lesson.is_published,
        )

    async def reorder_lessons(
            self,
            request: Request,
            module_id: int,
            data: LessonReorderRequest,
            course_slug: str | None = None,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> LessonsAdminResponse:
        """ПЕРЕСТАНОВКА УРОКОВ МОДУЛЯ

        Работает так же, как перестановка модулей: клиент присылает
        id уроков в новом порядке, позиции переназначаются 1..N
        одной транзакцией.
        """

        from app.api.v1.schemas.courses import LessonAdminResponse

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        module = await self._get_module_admin(
            request=request,
            module_id=module_id,
            error=error,
        )

        # если курс указан, модуль должен принадлежать ему
        if course_slug is not None:
            course = await self._get_course_admin(
                request=request,
                course_slug=course_slug,
                error=error,
            )

            if module.course_id != course.course_id:
                await self._raise(
                    request=request,
                    code="MODULE_NOT_FOUND",
                    error=error,
                )

        else:
            # курс нужен для пути файла урока
            course = await self._get_course_admin(
                request=request,
                course_slug=str(module.course_id),
                error=error,
            )

        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.module_id == module.module_id)
        )
        lessons = {lesson.lesson_id: lesson for lesson in result.scalars().all()}

        lesson_ids = data.lesson_ids

        # все переданные id должны существовать и принадлежать этому модулю
        if len(lesson_ids) != len(set(lesson_ids)) or set(lesson_ids) != set(lessons.keys()):
            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        await self._apply_positions(
            entities=lessons,
            ordered_ids=lesson_ids,
        )

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()

            await self._raise(
                request=request,
                code="UPDATE_ME_FAILED",
                error=error,
            )

        items = []

        for lesson in sorted(lessons.values(), key=lambda item: item.position):
            file_path = lesson_content_path(
                course_id=course.course_id,
                module_id=module.module_id,
                lesson_id=lesson.lesson_id,
            )

            has_content = False

            if file_path is not None:
                has_content = await minio_storage.exists(
                    file_path=file_path,
                    bucket=COURSE_CONTENT_BUCKET,
                )

            items.append(
                LessonAdminResponse(
                    success=True,
                    lesson_id=lesson.lesson_id,
                    id=lesson.lesson_id,
                    module_id=lesson.module_id,
                    title=lesson.title,
                    description=lesson.description,
                    position=lesson.position,
                    is_published=lesson.is_published,
                    is_active=lesson.is_published,
                    has_content=has_content,
                )
            )

        return LessonsAdminResponse(
            lessons=items,
            total_pages=1,
            current_page=1,
            page_size=len(items),
        )

    async def delete_lesson(
            self,
            request: Request,
            lesson_id: int,
            module_id: int | None = None,
            course_slug: str | None = None,
            language: str = "en",
            device_id: str | None = None,
            session_id: int | None = None,
            user_id: int | None = None,
            platform: str | None = None,
    ) -> EnrollmentResponse:
        """УДАЛЯЕТ УРОК И ЕГО ФАЙЛ В ХРАНИЛИЩЕ

        Запись в БД удаляется первой: если файл в хранилище почему-то
        не удалится, останется лишний файл, а не урок без текста.
        """

        error = self._error(
            language=language,
            device_id=device_id,
            session_id=session_id,
            user_id=user_id,
            platform=platform,
        )

        if module_id is not None:
            module = await self._get_module_admin(
                request=request,
                module_id=module_id,
                error=error,
            )

        else:
            # модуль нужен для проверки прав и пути файла
            module = await self._get_lesson_module(
                request=request,
                lesson_id=lesson_id,
                error=error,
            )

        # если курс указан, модуль должен принадлежать ему
        if course_slug is not None:
            course = await self._get_course_admin(
                request=request,
                course_slug=course_slug,
                error=error,
            )

            if module.course_id != course.course_id:
                await self._raise(
                    request=request,
                    code="MODULE_NOT_FOUND",
                    error=error,
                )

        else:
            # курс нужен для пути файла урока
            course = await self._get_course_admin(
                request=request,
                course_slug=str(module.course_id),
                error=error,
            )

        lesson = await self._get_lesson_admin(
            request=request,
            module=module,
            lesson_id=lesson_id,
            error=error,
        )

        file_path = lesson_content_path(
            course_id=course.course_id,
            module_id=module.module_id,
            lesson_id=lesson.lesson_id,
        )

        await self.db.delete(lesson)
        await self.db.commit()

        # позиции оставшихся уроков сдвигаем, чтобы не было пропусков
        await self._renumber_lessons(module=module)

        if file_path is not None:
            await minio_storage.delete_file(
                file_path=file_path,
                bucket=COURSE_CONTENT_BUCKET,
            )

        return EnrollmentResponse(success=True)

    async def _get_lesson_module(
            self,
            request: Request,
            lesson_id: int | str,
            error: dict,
    ) -> CourseModule:
        """МОДУЛЬ УРОКА

        Нужен, когда урок известен, а модуль — нет.
        """

        if not str(lesson_id).isdigit():
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        result = await self.db.execute(
            select(CourseModule)
            .join(Lesson, Lesson.module_id == CourseModule.module_id)
            .where(Lesson.lesson_id == int(lesson_id))
        )

        module = result.scalar_one_or_none()

        if module is None:
            await self._raise(
                request=request,
                code="LESSON_NOT_FOUND",
                error=error,
            )

        return module

    async def _renumber_lessons(self, module: CourseModule) -> None:
        """ПЕРЕНУМЕРОВЫВАЕТ УРОКИ МОДУЛЯ БЕЗ ПРОПУСКОВ

        После удаления урока позиции остальных сдвигаются,
        чтобы порядок остался 1..N.
        """

        result = await self.db.execute(
            select(Lesson)
            .where(Lesson.module_id == module.module_id)
            .order_by(Lesson.position)
        )

        lessons = result.scalars().all()

        if not lessons:
            return

        entities = {lesson.lesson_id: lesson for lesson in lessons}

        await self._apply_positions(
            entities=entities,
            ordered_ids=[lesson.lesson_id for lesson in lessons],
        )

        try:
            await self.db.commit()

        except IntegrityError:
            await self.db.rollback()
