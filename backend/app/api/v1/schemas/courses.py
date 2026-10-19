from pydantic import BaseModel, Field

# basic courses data
class CourseItem(BaseModel):
    slug: str
    title: str
    description: str | None = None
    main_image_url: str | None = None
    is_enrolled: bool = False

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

# basic lesson data
class LessonItem(BaseModel):
    lesson_id: int
    title: str
    description: str | None = None
    position: int

# detailed information about selected module
# returned only on page 1 of lessons
class ModuleInfo(BaseModel):
    module_id: int
    title: str
    description: str | None = None
    position: int
    content_url: str | None = None

# list of lessons of selected module
# at page 1 have ModuleInfo, next it = None
class LessonsResponse(BaseModel):
    module: ModuleInfo | None = None
    lessons: list[LessonItem] = Field(default_factory=list)
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

# result of the enrollment
class EnrollmentResponse(BaseModel):
    success: bool
# request for creating a course (admin)
class CourseCreateRequest(BaseModel):
    slug: str | None = Field(default=None, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    is_published: bool | None = None
    is_active: bool | None = None


# request for editing a course (admin)
class CourseUpdateRequest(BaseModel):
    slug: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    is_published: bool | None = None
    is_active: bool | None = None


# response for admin course create/edit
class CourseAdminResponse(CourseAdminItem):
    success: bool = True
    course_id: int
    id: int
    is_published: bool

# request for creating a module (admin)
class ModuleCreateRequest(BaseModel):
    course_id: int | None = None
    course_slug: str | None = Field(default=None, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    position: int | None = None
    is_published: bool | None = None
    is_active: bool | None = None


# request for editing a module (admin)
class ModuleUpdateRequest(BaseModel):
    course_id: int | None = None
    course_slug: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    position: int | None = None
    is_published: bool | None = None
    is_active: bool | None = None


# response for admin module create/edit/deactivate
class ModuleAdminResponse(BaseModel):
    success: bool = True
    module_id: int
    id: int
    course_id: int
    title: str
    description: str | None = None
    position: int
    is_published: bool
    is_active: bool

# admins list of modules
class ModulesAdminResponse(BaseModel):
    modules: list[ModuleAdminResponse] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int


# запрос на перестановку модулей курса
class ModuleReorderRequest(BaseModel):
    module_ids: list[int] = Field(..., min_length=1)

# request for reordering modules (admin)
class ModuleReorderRequest(BaseModel):
    module_ids: list[int] = Field(..., min_length=1)
