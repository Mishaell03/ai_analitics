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
