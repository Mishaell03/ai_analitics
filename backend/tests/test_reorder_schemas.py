import pytest
from pydantic import ValidationError

from app.api.v1.schemas.courses import LessonReorderRequest, ModuleReorderRequest


def test_module_reorder_request():
    request = ModuleReorderRequest(module_ids=[3, 1, 2])

    assert request.module_ids == [3, 1, 2]


def test_lesson_reorder_request():
    request = LessonReorderRequest(lesson_ids=[5, 6])

    assert request.lesson_ids == [5, 6]


def test_reorder_request_requires_ids():
    with pytest.raises(ValidationError):
        ModuleReorderRequest(module_ids=[])

    with pytest.raises(ValidationError):
        LessonReorderRequest(lesson_ids=[])
