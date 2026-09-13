from pydantic import BaseModel, Field

# basic courses data
class CourseItem(BaseModel):
    slug: str
    title: str
    description: str | None = None
    main_image_url: str | None = None

# users list of courses
class CoursesResponse(BaseModel):
    courses: list[CourseItem] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int

# admins courses data inheritance basic
class CourseAdminItem(CourseItem):
    is_active: bool

# admins list of courses
class CoursesAdminResponse(BaseModel):
    courses: list[CourseAdminItem] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int

# more info about course
class CourseInfo(CourseItem):
    content_url: str | None = None

# info about modules
class ModuleItem(BaseModel):
    module_id: int
    title: str
    description: str | None = None
    position: int
    content_url: str | None = None

# info about course id (at page 1 have CourseInfo, next it = None)
class CourseDetailResponse(BaseModel):
    course: CourseInfo | None = None
    modules: list[ModuleItem] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int


class CourseShortInfo(BaseModel):
    course_id: int
    slug: str
    title: str

class ModuleShortInfo(BaseModel):
    module_id: int
    title: str
    position: int

class LessonInfo(BaseModel):
    lesson_id: int
    title: str
    description: str | None = None
    position: int
    content_url: str | None = None

class LessonDetailResponse(BaseModel):
    course: CourseShortInfo
    module: ModuleShortInfo
    lesson: LessonInfo
