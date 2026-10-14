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