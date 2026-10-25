"""Нормализация и ранжирование поиска по каталогу курсов."""

import unicodedata
from collections.abc import Iterable


def normalize_search_text(value: str | None) -> str:
    """Сводит регистр и любое количество пробельных символов к одному пробелу."""

    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    return " ".join(normalized.split())


def _trigrams(value: str) -> set[str]:
    padded = f"  {value} "
    return {padded[index:index + 3] for index in range(len(padded) - 2)}


def trigram_similarity(left: str, right: str) -> float:
    """Dice-оценка пересечения символьных триграмм двух строк."""

    left_trigrams = _trigrams(left)
    right_trigrams = _trigrams(right)
    if not left_trigrams or not right_trigrams:
        return 0.0
    return 2 * len(left_trigrams & right_trigrams) / (
        len(left_trigrams) + len(right_trigrams)
    )


def _field_score(query: str, value: str) -> float:
    if not value:
        return 0.0
    if value == query:
        return 4.0
    if value.startswith(query):
        return 3.0 + len(query) / max(len(value), 1)
    if query in value:
        return 2.0 + len(query) / max(len(value), 1)

    # Слова позволяют искать короткую часть заголовка и исправлять ошибки
    # внутри отдельного слова, не размывая оценку длинным описанием.
    parts = value.split()
    best = trigram_similarity(query, value)
    for part in parts:
        best = max(best, trigram_similarity(query, part))
    return best


def course_search_score(query: str, title: str, description: str | None, slug: str) -> float:
    """Возвращает релевантность; точные/частичные совпадения заголовка выше."""

    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return 0.0

    normalized_title = normalize_search_text(title)
    normalized_description = normalize_search_text(description)
    normalized_slug = normalize_search_text(slug)
    if len(normalized_query) < 3 and not any(
        normalized_query in field
        for field in (normalized_title, normalized_description, normalized_slug)
    ):
        return 0.0
    return max(
        _field_score(normalized_query, normalized_title) * 1.0,
        _field_score(normalized_query, normalized_description) * 0.72,
        _field_score(normalized_query, normalized_slug) * 0.65,
    )


def rank_courses(query: str, courses: Iterable) -> list:
    """Возвращает только релевантные курсы, отсортированные по оценке и ID."""

    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return list(courses)

    # Минимальный порог исключает случайные совпадения на коротких строках,
    # при этом значения от 3 символов сохраняют fuzzy-поиск по опечаткам.
    threshold = 0.22 if len(normalized_query) >= 3 else 0.0
    scored = []
    for course in courses:
        score = course_search_score(
            normalized_query,
            course.title,
            course.description,
            course.slug,
        )
        if score >= threshold and score > 0:
            scored.append((score, course.course_id, course))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [course for _, _, course in scored]
