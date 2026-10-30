"""Разметка выбора одного ответа не содержит правильных ответов."""

import pytest
from fastapi import HTTPException

from app.api.v1.services.lesson_code_content import validate_blocks
from app.core.markdown import MarkdownParser


def test_single_choice_keeps_options_without_answers():
    source = ":::test\nid: single\nВыберите один\n- ( ) Один\n- ( ) Два\n:::\n"
    parsed = validate_blocks(source, [])
    assert parsed.content == source
    assert parsed.custom_blocks[0].data["exercise_id"] == "single"
    assert "- ( ) Один" in parsed.custom_blocks[0].data["body"]


@pytest.mark.parametrize("option", ["- (x) Один", "- (X) Один", "- (х) Один", "- (Х) Один", "- [x] Один", "- [х] Один"])
def test_server_rejects_answers_in_markdown(option):
    source = f":::test\nid: single\n{option}\n:::\n"
    with pytest.raises(ValueError, match="database"):
        MarkdownParser().parse(source)
    with pytest.raises(HTTPException) as exc:
        validate_blocks(source, [])
    assert exc.value.status_code == 422


def test_server_rejects_mixed_choice_options():
    with pytest.raises(HTTPException) as exc:
        validate_blocks(":::test\nid: mixed\n- ( ) Один\n- [ ] Два\n:::", [])
    assert exc.value.status_code == 422
