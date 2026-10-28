/**
 * СЕРВИС ОБРАБОТКИ MARKDOWN УРОКА
 *
 * Единая точка, где Markdown превращается в готовое к отрисовке
 * дерево блоков. React-компоненты только показывают результат и
 * ничего не разбирают сами.
 *
 * Сервис отвечает за:
 *
 *     * разбор блочной и инлайн-разметки;
 *     * безопасность ссылок (никаких javascript: и data:);
 *     * подсветку синтаксиса в блоках кода;
 *     * кастомные блоки (:::test, :::video, ...).
 *
 * Расширение под новые блоки:
 *
 *     markdownService.registerCustomBlock(new MyBlockHandler());
 *
 * Обработчик наследует CustomBlockHandler и описывает parse():
 * он превращает содержимое блока в данные (data), которые потом
 * покажет React-компонент.
 */

import {
    CustomBlockHandler,
    CustomBlockRegistry,
    PlaceholderCustomBlockHandler,
    TestBlockHandler,
    CodeBlockHandler,
} from "./customBlocks.js";
import {MarkdownParser} from "./parser.js";
import {codeHighlighter} from "./highlight.js";
import {isSafeUrl, safeUrl} from "./sanitize.js";
import {parseInline} from "./inline.js";

export class MarkdownService {
    /**
     * @param {object} options зависимости сервиса
     * @param {MarkdownParser} options.parser парсер блоков
     */
    constructor({parser} = {}) {
        this._parser = parser ?? new MarkdownParser();

        // задание — собственный тип блока: у него есть идентификатор
        this.registerCustomBlock(new TestBlockHandler());
        this.registerCustomBlock(new CodeBlockHandler());
    }

    /**
     * Разбирает Markdown урока.
     *
     * @param {string} source исходный Markdown
     * @returns {object[]} блоки урока
     */
    parse(source) {
        return this._parser.parse(source);
    }

    /**
     * Регистрирует обработчик кастомного блока.
     *
     * @param {CustomBlockHandler} handler обработчик типа блока
     * @returns {MarkdownService}
     */
    registerCustomBlock(handler) {
        this._parser.customBlocks.register(handler);

        return this;
    }

    /**
     * Подсвечивает код блока.
     *
     * @param {string} code исходный код
     * @param {string} language имя языка
     * @returns {{type: string, value: string}[]}
     */
    highlight(code, language) {
        return codeHighlighter.highlight(code, language);
    }
}

export const markdownService = new MarkdownService();

export {
    CustomBlockHandler,
    CustomBlockRegistry,
    PlaceholderCustomBlockHandler,
    TestBlockHandler,
    isSafeUrl,
    safeUrl,
    parseInline,
};
