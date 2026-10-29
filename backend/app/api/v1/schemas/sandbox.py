"""ЗАПРОСЫ И РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ PYTHON"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.api.v1.schemas.exercises import EXERCISE_ID_PATTERN
from app.services.sandbox.config import MAX_CODE_BYTES


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
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    duration: float
    output_limited: bool = False
    memory_limited: bool = False

    @computed_field
    @property
    def success(self) -> bool:
        return (self.exit_code == 0 and not self.timed_out
                and not self.output_limited and not self.memory_limited)


class ExerciseSubmitRequest(CodeRequest):
    language: Literal["sql", "python"]


class SandboxExecuteResponse(ExecutionResult):
    is_correct: bool | None


class StudentExerciseResponse(BaseModel):
    exercise_id: str
    body: str
    language: Literal["sql", "python"] | None = None
    execution_enabled: bool = False
    is_completed: bool = False


class ExpertSolutionResponse(BaseModel):
    exercise_id: str
    language: Literal["sql", "python"]
    code: str


class ExerciseSubmissionResponse(BaseModel):
    execution: ExecutionResult
    execution_succeeded: bool
    is_correct: bool | None
    attempt_id: int

    @computed_field
    @property
    def success(self) -> bool:
        return self.execution.success
