"""ЗАПРОСЫ И РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ PYTHON"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.api.v1.schemas.exercises import EXERCISE_ID_PATTERN
from app.services.sandbox.config import MAX_CODE_BYTES
from app.services.sandbox.plots import MAX_PLOTS, validate_png, validate_chart_data


class CodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=MAX_CODE_BYTES)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_CODE_BYTES or not value.strip():
            raise ValueError("Source is empty or too large")
        return value


class SandboxExecuteRequest(CodeRequest):
    language: Literal["sql", "python"] = "python"
    course_slug: str = Field(min_length=1, max_length=255)
    module_id: int = Field(gt=0)
    lesson_id: int = Field(gt=0)
    exercise_id: str = Field(min_length=1, max_length=64, pattern=EXERCISE_ID_PATTERN)


class RunnerExecutionRequest(CodeRequest):
    profile: Literal["light", "standard", "heavy"]
    language: Literal["python", "sql"] = "python"


class ExecutionResult(BaseModel):
    chart_data: list[dict] = Field(default_factory=list, max_length=MAX_PLOTS)
    plots: list[str] = Field(default_factory=list, max_length=MAX_PLOTS)
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration: float
    output_limited: bool = False
    memory_limited: bool = False

    @field_validator("plots")
    @classmethod
    def png_figures_only(cls, values):
        return [validate_png(value) for value in values]

    @field_validator("chart_data")
    @classmethod
    def bounded_chart_data(cls, values):
        return [validate_chart_data(value) for value in values]

    @computed_field
    @property
    def success(self) -> bool:
        return (self.exit_code == 0 and not self.timed_out
                and not self.output_limited and not self.memory_limited)


class ExerciseSubmitRequest(CodeRequest):
    language: Literal["sql", "python"]


class SandboxExecuteResponse(ExecutionResult):
    feedback: str | None = None
    is_correct: bool | None
    expert_solution_available: bool = False
    check_mode: Literal["graded", "self_review", "practice"] = "graded"


class StudentExerciseResponse(BaseModel):
    exercise_id: str
    body: str
    language: Literal["sql", "python"] | None = None
    execution_enabled: bool = False
    is_completed: bool = False
    expert_solution_available: bool = False


class ExpertSolutionResponse(BaseModel):
    exercise_id: str
    language: Literal["sql", "python"]
    code: str


class ExerciseSubmissionResponse(BaseModel):
    feedback: str | None = None
    execution: ExecutionResult
    execution_succeeded: bool
    is_correct: bool | None
    attempt_id: int
    expert_solution_available: bool = False
    check_mode: Literal["graded", "self_review", "practice"] = "graded"

    @computed_field
    @property
    def success(self) -> bool:
        return self.execution.success
