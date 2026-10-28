"""Bounded backend memory for the stateless DeepSeek API."""

import hashlib
import json
import re
from copy import deepcopy

LESSON_CHARS = 2400
HISTORY_TURNS = 10
HISTORY_QUESTION_CHARS = 200
HISTORY_ANSWER_CHARS = 350


def lesson_excerpt(text: str, question: str) -> str:
    """Local lexical retrieval without additional API calls or embeddings."""
    if len(text) <= LESSON_CHARS:
        return text
    words = set(re.findall(r"[\w]{3,}", question.lower()))
    chunks = [text[index:index + 780] for index in range(0, len(text), 780)]
    ranked = sorted(range(1, len(chunks)), key=lambda i: (
        -len(words & set(re.findall(r"[\w]{3,}", chunks[i].lower()))), i,
    ))
    selected = sorted([0, *ranked[:2]])
    return "\n[…]\n".join(chunks[index] for index in selected)[:LESSON_CHARS]


def context_fingerprint(system: str, metadata: dict, full_lesson: str, model: str) -> str:
    data = {"system": system, "metadata": metadata, "lesson": full_lesson, "model": model, "provider": "deepseek"}
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def memory_matches(state: dict, fingerprint: str) -> bool:
    """Do not import old provider memory or memory from an edited lesson/prompt."""
    return state.get("provider") == "deepseek" and state.get("fingerprint") == fingerprint


def compact_context(context: dict, instructions: str, max_bytes: int) -> dict:
    """Trim optional context before rejecting a long question. Never alter the question."""
    result = deepcopy(context)
    result["history"] = [
        {"question": item["question"][:HISTORY_QUESTION_CHARS], "answer": item["answer"][:HISTORY_ANSWER_CHARS]}
        for item in result.get("history", [])[-HISTORY_TURNS:]
    ]

    def size():
        return len((instructions + json.dumps(result, ensure_ascii=False, separators=(",", ":"))).encode("utf-8"))

    if size() <= max_bytes:
        return result
    # Preserve a small excerpt and some memory if possible; avoid slicing UTF-8 bytes.
    for container, key, minimum in ((result["lesson"], "text", 200), (result, "summary", 200),
                                    (result["course"], "description", 0)):
        while size() > max_bytes and len(container[key]) > minimum:
            container[key] = container[key][:max(minimum, len(container[key]) // 2)]
            if key == "text":
                result["lesson"]["text_truncated"] = True
    # Keep the most recent turns rather than dropping the entire dialogue at once.
    while size() > max_bytes and result["history"]:
        result["history"].pop(0)
    # The final provider guard handles a question/system prompt that alone exceeds the budget.
    return result
