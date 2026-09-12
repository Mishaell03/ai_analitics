from pydantic import BaseModel, Field

class CourseItem(BaseModel):
    slug: str
    title: str
    description: str | None = None
    main_image_url: str | None = None

class CoursesResponse(BaseModel):
    courses: list[CourseItem] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int

class CourseAdminItem(CourseItem):
    is_active: bool

class CoursesAdminResponse(BaseModel):
    courses: list[CourseAdminItem] = Field(default_factory=list)
    total_pages: int
    current_page: int
    page_size: int
