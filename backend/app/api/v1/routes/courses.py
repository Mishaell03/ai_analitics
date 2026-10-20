from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.courses import (
    CoursesResponse,
    CourseDetailResponse,
    LessonDetailResponse,
    LessonContentResponse,
    LessonsResponse,
    EnrollmentResponse,
    CourseAdminResponse,
    CourseCreateRequest,
    CourseUpdateRequest,
    CoursesAdminResponse,
    EnrollmentResponse,
    ModuleAdminResponse,
    ModuleCreateRequest,
    ModuleReorderRequest,
    ModuleUpdateRequest,
    ModulesAdminResponse,
)
from app.api.v1.services.courses import BaseCoursesService
from app.api.v1.services.lesson_content import LessonContentService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_admin, get_current_user
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix='/courses')


@router.get("", response_model=CoursesResponse)
async def get_courses(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
):
    courses = await BaseCoursesService(db).get_courses(
        page=page,
        page_size=page_size,
        user_id=current.user.user_id,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_COURSES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform
    )

    return courses


@router.get("/{course_slug}", response_model=CourseDetailResponse)
async def get_course(
        course_slug: str,
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    course = await BaseCoursesService(db).get_course(
        course_slug=course_slug,
        page=page,
        page_size=page_size,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.get("/{course_slug}/modules/{module_id}", response_model=LessonsResponse )
async def get_lessons(
    course_slug: str,
    module_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current: CurrentUserContext = Depends(get_current_user),
):
    lessons = await BaseCoursesService(db).get_lessons(
        course_slug=course_slug,
        module_id=module_id,
        page=page,
        page_size=page_size,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_LESSONS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lessons


@router.get("/{course_slug}/modules/{module_id}/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    lesson = await BaseCoursesService(db).get_lesson(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_LESSON",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lesson


@router.get("/{course_slug}/modules/{module_id}/lessons/{lesson_id}/content", response_model=LessonContentResponse)
async def get_lesson_content(
        course_slug: str,
        module_id: int,
        lesson_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    lesson_content = await LessonContentService(db).get_lesson_content(
        course_slug=course_slug,
        module_id=module_id,
        lesson_id=lesson_id,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
        is_admin=current.user.is_admin,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_LESSON_CONTENT",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return lesson_content


@router.post('/enroll/{course_slug}', response_model=EnrollmentResponse)
async def enroll_course(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    result = await BaseCoursesService(db).enroll_course(
        course_slug=course_slug,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ENROLL_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )


    return result


# ---------- ALIASES (admin, /courses) ----------

@router.delete("/{course_slug}", response_model=EnrollmentResponse)
async def delete_course_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


@router.post("/{course_slug}/deactivate", response_model=CourseAdminResponse)
async def deactivate_course_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DEACTIVATE_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.post("/{course_slug}/activate", response_model=CourseAdminResponse)
async def activate_course_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ACTIVATE_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.get("/{course_slug}/modules", response_model=ModulesAdminResponse)
async def get_modules_alias3(
        course_slug: str,
        request: Request,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_MODULES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return modules


@router.post("/{course_slug}/modules", response_model=ModuleAdminResponse)
async def create_module_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/modules", response_model=ModuleAdminResponse)
async def create_module_flat_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.put("/{course_slug}/modules/reorder", response_model=EnrollmentResponse)
async def reorder_modules_alias3(
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
        event="SUCCESS_REORDER_MODULES",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result
@router.delete("/{course_slug}/modules/{module_id}", response_model=EnrollmentResponse)
async def delete_module_nested_alias3(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await delete_module_flat_alias3(module_id=module_id, request=request, db=db, current=current)


@router.post("/modules/{module_id}/deactivate", response_model=ModuleAdminResponse)
async def deactivate_module_flat_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DEACTIVATE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/modules/{module_id}/activate", response_model=ModuleAdminResponse)
async def activate_module_flat_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_ACTIVATE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.post("/{course_slug}/modules/{module_id}/deactivate", response_model=ModuleAdminResponse)
async def deactivate_module_nested_alias3(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await deactivate_module_flat_alias3(module_id=module_id, request=request, db=db, current=current)


@router.post("/{course_slug}/modules/{module_id}/activate", response_model=ModuleAdminResponse)
async def activate_module_nested_alias3(
        course_slug: str,
        module_id: int,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await activate_module_flat_alias3(module_id=module_id, request=request, db=db, current=current)
@router.post("", response_model=CourseAdminResponse)
async def create_course(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_CREATE_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.patch("/{course_slug}", response_model=CourseAdminResponse)
async def update_course(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return course


@router.put("/{course_slug}", response_model=CourseAdminResponse)
async def replace_course(
        course_slug: str,
        request: Request,
        data: CourseUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_course(
        course_slug=course_slug,
        request=request,
        data=data,
        db=db,
        current=current,
    )
@router.delete('/unenroll/{course_slug}', response_model=EnrollmentResponse)
async def unenroll_course(
        course_slug: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    result = await BaseCoursesService(db).unenroll_course(
        course_slug=course_slug,
        request=request,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UNENROLL_COURSE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result
@router.patch("/modules/{module_id}", response_model=ModuleAdminResponse)
async def update_module_flat_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_UPDATE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return module


@router.put("/modules/{module_id}", response_model=ModuleAdminResponse)
async def replace_module_flat_alias3(
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_module_flat_alias3(module_id=module_id, request=request, data=data, db=db, current=current)


@router.patch("/{course_slug}/modules/{module_id}", response_model=ModuleAdminResponse)
async def update_module_nested_alias3(
        course_slug: str,
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_module_flat_alias3(module_id=module_id, request=request, data=data, db=db, current=current)


@router.put("/{course_slug}/modules/{module_id}", response_model=ModuleAdminResponse)
async def replace_module_nested_alias3(
        course_slug: str,
        module_id: int,
        request: Request,
        data: ModuleUpdateRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    return await update_module_flat_alias3(module_id=module_id, request=request, data=data, db=db, current=current)


@router.delete("/modules/{module_id}", response_model=EnrollmentResponse)
async def delete_module_flat_alias3(
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
        user_id=current.user.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_DELETE_MODULE",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.user.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return result


