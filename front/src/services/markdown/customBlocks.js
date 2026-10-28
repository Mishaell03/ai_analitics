/**
 * ОБРАБОТЧИКИ КАСТОМНЫХ БЛОКОВ MARKDOWN
 *
 * Кастомный блок — фрагмент урока, который решается отдельно
 * от обычного Markdown: тест, видео, практическое задание.
 *
 * Разметка блока:
 *
 *     :::test
 *     Текст блока
 *     :::
 *
 * Чтобы добавить свой тип блока, достаточно:
 *
 *     1. унаследовать CustomBlockHandler и описать parse();
 *     2. зарегистрировать обработчик в реестре.
 *
 * Типы без собственного обработчика разбираются заглушкой:
 * содержимое отдаётся как есть.
 */

// идентификатор задания задаётся первой строкой содержимого блока
const EXERCISE_ID_LINE = /^id:\s*(?<exercise_id>[A-Za-z0-9_-]{1,64})\s*$/i;

export class CustomBlockHandler {
    /**
     * @param {string} type тип блока в разметке (test, video, ...)
     */
    constructor(type) {
        this.type = type;
    }

    /**
     * Разбирает содержимое блока.
     *
     * @param {string} content содержимое блока без разметки :::type
     * @returns {{type: string, content: string, implemented: boolean, data: object|null}}
     */
    parse(content) {
        return {
            type: this.type,
            content,
            implemented: false,
            data: null,
        };
    }
}

export class PlaceholderCustomBlockHandler extends CustomBlockHandler {
    /**
     * Заглушка: содержимое блока не интерпретируется.
     *
     * @param {string} content содержимое блока
     * @returns {{type: string, content: string, implemented: boolean, data: object|null}}
     */
    parse(content) {
        return {
            type: this.type,
            content,
            implemented: false,
            data: null,
        };
    }
}

export class TestBlockHandler extends CustomBlockHandler {
    /**
     * @param {string} type тип блока в разметке
     */
    constructor(type = "test") {
        super(type);
    }

    /**
     * Задание урока.
     *
     * Задание записывается в Markdown так:
     *
     *     :::test
     *     id: python-variables
     *     Текст задания
     *     - [ ] Вариант 1
     *     :::
     *
     * Идентификатор связывает задание с правильным ответом, который
     * хранится в базе. Правила разбора те же, что у backend.
     *
     * @param {string} content содержимое блока без разметки :::test
     * @returns {{type: string, content: string, implemented: boolean, data: object}}
     */
    parse(content) {
        const {exercise_id, body} = splitExerciseHeader(content);

        return {
            type: this.type,
            content,
            implemented: false,
            data: {
                exercise_id,
                body,
            },
        };
    }
}

/**
 * Отделяет идентификатор задания от текста.
 *
 * @param {string} content содержимое блока
 * @returns {{exercise_id: string|null, body: string}}
 */
export function splitExerciseHeader(content) {
    const lines = (content ?? "").split("\n");

    if (!lines.length) {
        return {exercise_id: null, body: content ?? ""};
    }

    const match = EXERCISE_ID_LINE.exec(lines[0]);

    if (!match) {
        return {exercise_id: null, body: content};
    }

    return {
        exercise_id: match.groups.exercise_id,
        body: lines.slice(1).join("\n").trim(),
    };
}

export class CodeBlockHandler extends CustomBlockHandler {
    constructor() {
        super("code");
    }

    parse(content) {
        const [header, ...lines] = content.split("\n");
        const language = header.replace(/^language: /, "");
        const {exercise_id, body} = splitExerciseHeader(lines.join("\n"));
        return {type: "code", content: "", implemented: true, data: {
            exercise_id, language,
            valid: ["sql", "python"].includes(language) && Boolean(exercise_id) && !body,
        }};
    }
}

export class CustomBlockRegistry {
    /**
     * @param {CustomBlockHandler[]} handlers обработчики типов блоков
     */
    constructor(handlers = []) {
        this._handlers = new Map();

        handlers.forEach((handler) => this.register(handler));
    }

    /**
     * Регистрирует обработчик типа блока.
     *
     * @param {CustomBlockHandler} handler обработчик
     * @returns {CustomBlockRegistry}
     */
    register(handler) {
        this._handlers.set(handler.type, handler);

        return this;
    }

    /**
     * Есть ли свой обработчик у типа блока.
     *
     * @param {string} type тип блока
     * @returns {boolean}
     */
    has(type) {
        return this._handlers.has(type);
    }

    /**
     * Разбирает блок нужным обработчиком.
     *
     * Для незарегистрированных типов используется заглушка.
     *
     * @param {string} type тип блока
     * @param {string} content содержимое блока
     * @returns {{type: string, content: string, implemented: boolean, data: object|null}}
     */
    parse(type, content) {
        const handler = this._handlers.get(type) ?? new PlaceholderCustomBlockHandler(type);

        return handler.parse(content);
    }
}
