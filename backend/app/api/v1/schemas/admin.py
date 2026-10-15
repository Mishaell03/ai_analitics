from datetime import datetime

from pydantic import BaseModel, Field


# последний зарегистрированный пользователь
class DashboardLatestUser(BaseModel):
    user_id: int
    name: str | None = None
    email: str
    created_at: datetime
    img_url: str | None = None


# самый популярный курс по количеству записей
class DashboardTopCourse(BaseModel):
    course_id: int
    title: str
    enrollments_count: int


# главная панель администратора
class DashboardResponse(BaseModel):
    total_users: int
    total_courses: int
    total_lessons: int
    total_enrollments: int
    total_active_sessions: int
    latest_users: list[DashboardLatestUser] = Field(default_factory=list)
    top_courses: list[DashboardTopCourse] = Field(default_factory=list)


# базовые данные пользователя
class _UsersBaseInfo(BaseModel):
    user_id: int
    name: str | None = None
    email: str
    phone: str | None = None
    img_url: str | None = None
    is_admin: bool = False
    is_blocked: bool = False


# пользователь списка + счётчики для карточки
class AdminUserItem(_UsersBaseInfo):
    created_at: datetime
    active_sessions: int = 0
    enrollments: int = 0


# способ входа пользователя
class AdminUserAuthMethod(BaseModel):
    provider: str
    provider_name: str | None = None
    provider_user_id: str | None = None
    created_at: datetime


# согласие на обработку персональных данных
class AdminUserConsent(BaseModel):
    consent_code: str
    is_accepted: bool
    policy_version: str | None = None
    ip: str | None = None
    accepted_at: datetime


# сессия пользователя
# страна и прокси берутся из последнего события сессии:
# в самой сессии геоданных нет, они пишутся в лог запросов
class AdminUserSession(BaseModel):
    session_id: int
    provider: str
    platform: str | None = None
    device_name: str | None = None
    device_id: str
    language: str
    ip: str | None = None
    country_code: str | None = None
    is_proxy: bool | None = None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    last_seen_at: datetime | None = None
    is_active: bool


# попытка решения урока
class AdminUserLessonAttempt(BaseModel):
    attempt_id: int
    lesson_id: int
    lesson_title: str
    code: str | None = None
    correctness: int
    speed: int
    created_at: datetime


# курс пользователя с прогрессом
class AdminUserCourseProgress(BaseModel):
    course_id: int
    slug: str
    title: str
    is_published: bool
    enrolled_at: datetime
    lessons_total: int = 0
    lessons_with_attempts: int = 0
    lessons_solved: int = 0
    attempts_total: int = 0


# сводка по обучению пользователя
class AdminUserLearningStats(BaseModel):
    enrollments: int = 0
    lessons_with_attempts: int = 0
    lessons_solved: int = 0
    attempts_total: int = 0
    last_attempt_at: datetime | None = None


# полная карточка пользователя
class AdminUserDetail(BaseModel):
    user: AdminUserItem
    total_sessions: int = 0
    active_sessions: int = 0
    learning: AdminUserLearningStats = Field(default_factory=AdminUserLearningStats)
    auth_methods: list[AdminUserAuthMethod] = Field(default_factory=list)
    consents: list[AdminUserConsent] = Field(default_factory=list)
    sessions: list[AdminUserSession] = Field(default_factory=list)
    courses: list[AdminUserCourseProgress] = Field(default_factory=list)
    recent_attempts: list[AdminUserLessonAttempt] = Field(default_factory=list)


# постраничный список пользователей админки
class AdminQuantityUsers(BaseModel):
    page: int
    page_size: int
    total_pages: int
    users: list[_UsersBaseInfo] = Field(default_factory=list)


# результат блокировки / разблокировки
class AdminUserBlockResponse(BaseModel):
    user_id: int
    is_blocked: bool
