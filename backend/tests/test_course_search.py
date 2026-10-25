from types import SimpleNamespace

from app.api.v1.services.course_search import (
    course_search_score,
    normalize_search_text,
    rank_courses,
    trigram_similarity,
)


def course(course_id: int, title: str, description: str = ""):
    return SimpleNamespace(
        course_id=course_id,
        title=title,
        description=description,
        slug=f"course-{course_id}",
    )


def test_exact_match_ranks_above_other_relevant_results():
    courses = [
        course(1, "Основы аналитики", "Введение"),
        course(2, "Аналитика", "Курс для начинающих"),
        course(3, "Аналитика данных", "Практика"),
    ]

    result = rank_courses("аналитика", courses)

    assert [item.course_id for item in result] == [2, 3, 1]


def test_trigram_search_finds_typo_in_cyrillic():
    matches = rank_courses("аналитка", [course(1, "Аналитика данных")])

    assert [item.course_id for item in matches] == [1]
    assert trigram_similarity("аналитка", "аналитика") > 0.5


def test_trigram_search_finds_typo_in_latin():
    matches = rank_courses("pythn", [course(1, "Python for analytics")])

    assert [item.course_id for item in matches] == [1]


def test_partial_input_and_case_insensitive_normalization():
    result = rank_courses("  PYTH  ", [course(1, "Python basics")])

    assert [item.course_id for item in result] == [1]
    assert normalize_search_text("  Data\t  Science  ") == "data science"


def test_short_queries_require_a_literal_partial_match():
    assert rank_courses("zz", [course(1, "Python basics")]) == []
    assert [item.course_id for item in rank_courses("py", [course(1, "Python basics")])] == [1]


def test_search_also_checks_description():
    assert course_search_score(
        "машинное обучение",
        "Искусственный интеллект",
        "Введение в машинное обучение",
        "ai-course",
    ) > 0


def test_empty_query_returns_courses_without_reordering_or_filtering():
    courses = [course(2, "Python"), course(1, "Аналитика")]

    assert rank_courses(" \t ", courses) == courses


def test_relevance_ties_are_stable_by_course_id():
    result = rank_courses("python", [course(9, "Python"), course(2, "Python")])

    assert [item.course_id for item in result] == [2, 9]


def test_sql_like_input_is_ordinary_text_not_a_pattern():
    assert rank_courses("%_'; DROP TABLE courses;--", [course(1, "Python")]) == []
