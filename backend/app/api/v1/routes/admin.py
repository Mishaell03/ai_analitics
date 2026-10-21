from datetime import date

from fastapi import APIRouter, Depends, File, Request, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin import (
    AdminQuantityUsers,
    AdminUserBlockResponse,
    AdminUserDetail,
    DashboardResponse,
)
from app.api.v1.schemas.media import (
    CourseImageResponse,
    MediaInfoResponse,
    MediaListResponse,
    MediaUrlResponse,
)
from app.api.v1.schemas.courses import (
    CourseAdminResponse,
    CourseCreateRequest,
    CourseUpdateRequest,
    CoursesAdminResponse,
    EnrollmentResponse,
    LessonAdminResponse,
    LessonContentResponse,
    LessonCreateRequest,
    LessonReorderRequest,
    LessonUpdateRequest,
    LessonUploadResponse,
    LessonsAdminResponse,
    ModuleAdminResponse,
    ModuleCreateRequest,
    ModuleReorderRequest,
    ModuleUpdateRequest,
    ModulesAdminResponse,
)
from app.api.v1.services.courses import BaseCoursesService
from app.api.v1.services.course_image import CourseImageService
from app.api.v1.services.lesson_admin import LessonAdminService
from app.api.v1.services.lesson_content import LessonContentService
from app.api.v1.services.lesson_media import LessonMediaService
from app.api.v1.services.admin import AdminService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_admin
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/admin")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
        request: Request,
        users: int | None = Query(default=None, description="Количество последних пользователей"),
        top_courses: int | None = Query(default=None, description="Количество курсов для аналитики"),
        # period: int | None = Query(default=None, description="Количество дней периода"),
        # date_of: date | None = Query(default=None, description="Начало периода"),
        # date_to: date | None = Query(default=None, description="Конец периода"),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    dashboard = await AdminService(db).get_dashboard(
        users=users,
        top_courses=top_courses,
        # period=period,
        # date_of=date_of,
        # date_to=date_to
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_DASHBOARD",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return dashboard


@router.get("/users", response_model=AdminQuantityUsers)
async def get_users(
        request: Request,
        page: int = Query(default=1, ge=1, description="Номер страницы"),
        per_page: int = Query(default=10, ge=1, le=100, description="Пользователей на странице"),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    users = await AdminService(db).get_users(
        page=page,
        per_page=per_page,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_USERS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return users


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    detail = await AdminService(db).get_user_detail(
        request=request,
        user_id=user_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        admin_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_USER_DETAIL",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return detail


@router.post("/users/{user_id}/block", response_model=AdminUserBlockResponse)
async def block_user(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await AdminService(db).set_user_blocked(
        request=request,
        user_id=user_id,
        is_blocked=True,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        admin_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_BLOCK_ADMIN_USER",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


# ---------- COURSES: DELETE / DEACTIVATE / ACTIVATE ----------

@router.delete("/courses/{course_slug}", response_model=EnrollmentResponse)
async def delete_admin_course(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).delete_course(
        request=request,
        course_slug=course_slug,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.post("/courses/{course_slug}/deactivate", response_model=CourseAdminResponse)
async def deactivate_admin_course(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    course = await BaseCoursesService(db).deactivate_course(
        request=request,
        course_slug=course_slug,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DEACTIVATE_ADMIN_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.post("/courses/{course_slug}/activate", response_model=CourseAdminResponse)
async def activate_admin_course(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    course = await BaseCoursesService(db).activate_course(
        request=request,
        course_slug=course_slug,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ACTIVATE_ADMIN_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


# ---------- MODULES ----------

@router.get("/courses/{course_slug}/modules", response_model=ModulesAdminResponse)
async def get_admin_modules(
        course_slug: str,
        request: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    modules = await BaseCoursesService(db).get_modules_admin(
        course_slug=course_slug,
        request=request,
        page=page,
        page_size=page_size,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_MODULES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return modules


@router.post("/courses/{course_slug}/modules", response_model=ModuleAdminResponse)
async def create_admin_module_nested(
        course_slug: str,
        request: Request,
        data: ModuleCreateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    module = await BaseCoursesService(db).create_module(
        request=request,
        course_slug=course_slug,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/modules", response_model=ModuleAdminResponse)
async def create_admin_module_flat(
        request: Request,
        data: ModuleCreateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    module = await BaseCoursesService(db).create_module(
        request=request,
        course_slug=None,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.patch("/modules/{module_id}", response_model=ModuleAdminResponse)
async def update_admin_module_flat(
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    module = await BaseCoursesService(db).update_module(
        request=request,
        module_id=module_id,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.put("/modules/{module_id}", response_model=ModuleAdminResponse)
async def replace_admin_module_flat(
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_admin_module_flat(
        module_id=module_id,
        request=request,
        data=data,
        db=db,
        current=current,
    )


@router.put("/courses/{course_slug}/modules/reorder", response_model=ModulesAdminResponse)
async def reorder_admin_modules(
        course_slug: str,
        request: Request,
        data: ModuleReorderRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).reorder_modules(
        request=request,
        course_slug=course_slug,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_REORDER_ADMIN_MODULES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.put("/courses/{course_slug}/modules/{module_id}/lessons/reorder", response_model=LessonsAdminResponse)
async def reorder_admin_lessons(
        course_slug: str,
        module_id: int,
        request: Request,
        data: LessonReorderRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).reorder_lessons(
        request=request,
        module_id=module_id,
        data=data,
        course_slug=course_slug,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_REORDER_ADMIN_LESSONS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.put("/modules/{module_id}/lessons/reorder", response_model=LessonsAdminResponse)
async def reorder_admin_lessons_flat(
        module_id: int,
        request: Request,
        data: LessonReorderRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).reorder_lessons(
        request=request,
        module_id=module_id,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_REORDER_ADMIN_LESSONS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.patch("/courses/{course_slug}/modules/{module_id}", response_model=ModuleAdminResponse)
async def update_admin_module_nested(
        course_slug: str,
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_admin_module_flat(
        module_id=module_id,
        request=request,
        data=data,
        db=db,
        current=current,
    )


@router.put("/courses/{course_slug}/modules/{module_id}", response_model=ModuleAdminResponse)
async def replace_admin_module_nested(
        course_slug: str,
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_admin_module_flat(
        module_id=module_id,
        request=request,
        data=data,
        db=db,
        current=current,
    )


@router.delete("/modules/{module_id}", response_model=EnrollmentResponse)
async def delete_admin_module_flat(
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).delete_module(
        request=request,
        module_id=module_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.delete("/courses/{course_slug}/modules/{module_id}", response_model=EnrollmentResponse)
async def delete_admin_module_nested(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await delete_admin_module_flat(
        module_id=module_id,
        request=request,
        db=db,
        current=current,
    )


@router.post("/modules/{module_id}/deactivate", response_model=ModuleAdminResponse)
async def deactivate_admin_module_flat(
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    module = await BaseCoursesService(db).deactivate_module(
        request=request,
        module_id=module_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DEACTIVATE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/modules/{module_id}/activate", response_model=ModuleAdminResponse)
async def activate_admin_module_flat(
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    module = await BaseCoursesService(db).activate_module(
        request=request,
        module_id=module_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ACTIVATE_ADMIN_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/courses/{course_slug}/modules/{module_id}/deactivate", response_model=ModuleAdminResponse)
async def deactivate_admin_module_nested(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await deactivate_admin_module_flat(
        module_id=module_id,
        request=request,
        db=db,
        current=current,
    )


@router.post("/courses/{course_slug}/modules/{module_id}/activate", response_model=ModuleAdminResponse)
async def activate_admin_module_nested(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await activate_admin_module_flat(
        module_id=module_id,
        request=request,
        db=db,
        current=current,
    )
@router.get("/courses", response_model=CoursesAdminResponse)
async def get_admin_courses(
        request: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    courses = await BaseCoursesService(db).get_courses_admin(
        page=page,
        page_size=page_size,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_COURSES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return courses


@router.post("/courses", response_model=CourseAdminResponse)
async def create_admin_course(
        request: Request,
        data: CourseCreateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    course = await BaseCoursesService(db).create_course(
        request=request,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_ADMIN_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.patch("/courses/{course_slug}", response_model=CourseAdminResponse)
async def update_admin_course(
        course_slug: str,
        request: Request,
        data: CourseUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    course = await BaseCoursesService(db).update_course(
        request=request,
        course_slug=course_slug,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_ADMIN_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.put("/courses/{course_slug}", response_model=CourseAdminResponse)
async def replace_admin_course(
        course_slug: str,
        request: Request,
        data: CourseUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_admin_course(
        course_slug=course_slug,
        request=request,
        data=data,
        db=db,
        current=current,
    )


# ---------- LESSONS ----------

@router.get("/courses/{course_slug}/modules/{module_id}/lessons", response_model=LessonsAdminResponse)
async def get_admin_lessons(
        course_slug: str,
        module_id: int,
        request: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    lessons = await BaseCoursesService(db).get_lessons_admin(
        course_slug=course_slug,
        module_id=module_id,
        request=request,
        page=page,
        page_size=page_size,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_LESSONS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lessons


@router.get(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/content",
    response_model=LessonContentResponse,
)
async def get_admin_lesson_content(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    content = await LessonContentService(db).get_lesson_content_admin(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_LESSON_CONTENT",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return content


@router.post(
    "/courses/{course_slug}/modules/{module_id}/lessons",
    response_model=LessonAdminResponse,
)
async def create_admin_lesson(
        course_slug: str,
        module_id: int,
        request: Request,
        data: LessonCreateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    lesson = await LessonAdminService(db).create_lesson(
        course_slug=course_slug,
        module_id=module_id,
        data=data,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_ADMIN_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lesson


@router.post(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/upload-url",
    response_model=LessonUploadResponse,
)
async def get_admin_lesson_upload_url(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    upload = await LessonAdminService(db).get_lesson_upload_url(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_LESSON_UPLOAD_URL",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return upload


@router.patch(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}",
    response_model=LessonAdminResponse,
)
async def update_admin_lesson(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        data: LessonUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    lesson = await BaseCoursesService(db).update_lesson(
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        data=data,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_ADMIN_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lesson


@router.delete(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}",
    response_model=EnrollmentResponse,
)
async def delete_admin_lesson(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).delete_lesson(
        module_id=module_id,
        lesson_id=lesson_id,
        course_slug=course_slug,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.delete(
    "/lessons/{lesson_id}",
    response_model=EnrollmentResponse,
)
async def delete_admin_lesson_flat(
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await BaseCoursesService(db).delete_lesson(
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


# ---------- MEDIA ----------

@router.post(
    "/courses/{course_slug}/image",
    response_model=CourseImageResponse,
)
async def upload_admin_course_image(
        course_slug: str,
        request: Request,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    image = await CourseImageService(db).upload_image(
        course_slug=course_slug,
        file=file,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPLOAD_ADMIN_COURSE_IMAGE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return image


@router.get(
    "/courses/{course_slug}/image",
    response_model=CourseImageResponse,
)
async def get_admin_course_image(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    image = await CourseImageService(db).get_image(
        course_slug=course_slug,
        request=request,
        is_admin=True,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_COURSE_IMAGE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return image


@router.delete(
    "/courses/{course_slug}/image",
    response_model=CourseImageResponse,
)
async def delete_admin_course_image(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    image = await CourseImageService(db).delete_image(
        course_slug=course_slug,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_COURSE_IMAGE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return image


@router.post(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media",
    response_model=MediaInfoResponse,
)
async def upload_admin_lesson_media(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).upload_media(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        file=file,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPLOAD_ADMIN_LESSON_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.get(
    "/courses/{course_slug}/modules/{module_id}/lessons/{lesson_id}/media",
    response_model=MediaListResponse,
)
async def get_admin_lesson_media(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).list_media(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        page=page,
        page_size=page_size,
        is_admin=True,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_LESSON_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.get("/media/{media_key}", response_model=MediaInfoResponse)
async def get_admin_media(
        media_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).get_media(
        media_key=media_key,
        request=request,
        is_admin=True,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.post("/media/{media_key}/url", response_model=MediaUrlResponse)
async def get_admin_media_url(
        media_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    url = await LessonMediaService(db).get_media_url(
        media_key=media_key,
        request=request,
        is_admin=True,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_MEDIA_URL",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return url


@router.delete("/media/{media_key}", response_model=MediaListResponse)
async def delete_admin_media(
        media_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).delete_media(
        media_key=media_key,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.post(
    "/lessons/{lesson_id}/media/{media_key}",
    response_model=MediaInfoResponse,
)
async def attach_admin_lesson_media(
        lesson_id: int,
        media_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).attach_media(
        lesson_id=lesson_id,
        media_key=media_key,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ATTACH_ADMIN_LESSON_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.delete(
    "/lessons/{lesson_id}/media/{media_key}",
    response_model=MediaListResponse,
)
async def delete_admin_lesson_media(
        lesson_id: int,
        media_key: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    media = await LessonMediaService(db).delete_media(
        media_key=media_key,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_ADMIN_LESSON_MEDIA",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return media


@router.delete("/users/{user_id}/block", response_model=AdminUserBlockResponse)
async def unblock_user(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    result = await AdminService(db).set_user_blocked(
        request=request,
        user_id=user_id,
        is_blocked=False,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        admin_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UNBLOCK_ADMIN_USER",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result