/**
 * РАЗБОР MARKDOWN УРОКА НА БЛОКИ
 *
 * Урок превращается в дерево блоков: заголовки, абзацы, списки,
 * таблицы, цитаты, блоки кода, разделители, картинки и кастомные
 * блоки (:::test, :::video, ...).
 *
 * Сервис ничего не знает о React: разметку собирает компонент,
 * поэтому содержимое урока не может превратиться в исполняемый код.
 */

import {CustomBlockRegistry} from "./customBlocks.js";
import {parseInline} from "./inline.js";
import {codeHighlighter} from "./highlight.js";

const FENCE_PATTERN = /^(\s{0,3})(`{3,}|~{3,})\s*([^`\s]*)\s*$/;
const HEADING_PATTERN = /^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$/;
const THEMATIC_BREAK_PATTERN = /^\s{0,3}([-*_])(\s*\1){2,}\s*$/;
const LIST_ITEM_PATTERN = /^(\s*)([-*+]|\d{1,9}[.)])\s+(.*)$/;
const QUOTE_PATTERN = /^\s{0,3}>\s?(.*)$/;
const TABLE_DIVIDER_PATTERN = /^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$/;
const SETEXT_PATTERN = /^\s{0,3}(=+|-+)\s*$/;
const CUSTOM_BLOCK_OPEN_PATTERN = /^\s{0,3}:::\s*([a-zA-Z][a-zA-Z0-9_-]*)\s*$/;
const CUSTOM_BLOCK_CLOSE_PATTERN = /^\s{0,3}:::\s*$/;
const INDENTED_CODE_PATTERN = /^\s{4,}\S/;

const BLOCK_CODE = "code";
const BLOCK_CUSTOM = "custom";
const BLOCK_DIVIDER = "divider";
const BLOCK_HEADING = "heading";
const BLOCK_LIST = "list";
const BLOCK_PARAGRAPH = "paragraph";
const BLOCK_QUOTE = "quote";
const BLOCK_TABLE = "table";

export class MarkdownParser {
    /**
     * @param {object} options зависимости парсера
     * @param {CustomBlockRegistry} options.customBlocks реестр кастомных блоков
     * @param {{highlight: function(string, string): object[]}} options.highlighter подсветка кода
     */
    constructor({customBlocks = new CustomBlockRegistry(), highlighter = codeHighlighter} = {}) {
        this._customBlocks = customBlocks;
        this._highlighter = highlighter;
    }

    /**
     * Реестр кастомных блоков парсера.
     *
     * @returns {CustomBlockRegistry}
     */
    get customBlocks() {
        return this._customBlocks;
    }

    /**
     * Разбирает Markdown урока.
     *
     * @param {string} source исходный Markdown
     * @returns {object[]} блоки урока
     */
    parse(source) {
        if (!source) {
            return [];
        }

        const lines = source.replace(/\r\n?/g, "\n").split("\n");

        return this._parseBlocks(lines);
    }

    _parseBlocks(lines) {
        const blocks = [];
        let index = 0;

        while (index < lines.length) {
            const line = lines[index];

            if (!line.trim()) {
                index += 1;
                continue;
            }

            const custom = this._parseCustomBlock(lines, index);

            if (custom) {
                blocks.push(custom.block);
                index = custom.nextIndex;
                continue;
            }

            const fence = this._parseFence(lines, index);

            if (fence) {
                blocks.push(fence.block);
                index = fence.nextIndex;
                continue;
            }

            if (THEMATIC_BREAK_PATTERN.test(line)) {
                blocks.push({type: BLOCK_DIVIDER});
                index += 1;
                continue;
            }

            const heading = HEADING_PATTERN.exec(line);

            if (heading) {
                blocks.push({
                    type: BLOCK_HEADING,
                    level: heading[1].length,
                    children: parseInline(heading[2]),
                });
                index += 1;
                continue;
            }

            if (QUOTE_PATTERN.test(line)) {
                const quote = this._parseQuote(lines, index);
                blocks.push(quote.block);
                index = quote.nextIndex;
                continue;
            }

            if (LIST_ITEM_PATTERN.test(line)) {
                const list = this._parseList(lines, index);
                blocks.push(list.block);
                index = list.nextIndex;
                continue;
            }

            if (this._isTableStart(lines, index)) {
                const table = this._parseTable(lines, index);
                blocks.push(table.block);
                index = table.nextIndex;
                continue;
            }

            const paragraph = this._parseParagraph(lines, index);
            blocks.push(paragraph.block);
            index = paragraph.nextIndex;
        }

        return blocks;
    }

    _parseCustomBlock(lines, start) {
        const match = CUSTOM_BLOCK_OPEN_PATTERN.exec(lines[start]);

        if (!match) {
            return null;
        }

        const body = [];
        let index = start + 1;
        let closed = false;

        while (index < lines.length) {
            if (CUSTOM_BLOCK_CLOSE_PATTERN.test(lines[index])) {
                closed = true;
                index += 1;
                break;
            }

            body.push(lines[index]);
            index += 1;
        }

        // незакрытый блок — обычный текст
        if (!closed) {
            return null;
        }

        const content = body.join("\n");
        const parsed = this._customBlocks.parse(match[1], content);

        return {
            block: {
                type: BLOCK_CUSTOM,
                blockType: match[1],
                content,
                implemented: Boolean(parsed.implemented),
                data: parsed.data ?? null,
                children: this._parseBlocks(body),
            },
            nextIndex: index,
        };
    }

    _parseFence(lines, start) {
        const match = FENCE_PATTERN.exec(lines[start]);

        if (!match) {
            return null;
        }

        const marker = match[2];
        const language = match[3] ?? "";
        const code = [];

        let index = start + 1;
        const closing = new RegExp(`^\\s{0,3}${marker[0]}{${marker.length},}\\s*$`);

        while (index < lines.length) {
            if (closing.test(lines[index])) {
                index += 1;
                break;
            }

            code.push(lines[index]);
            index += 1;
        }

        const source = code.join("\n");

        return {
            block: {
                type: BLOCK_CODE,
                language,
                code: source,
                tokens: this._highlighter.highlight(source, language),
            },
            nextIndex: index,
        };
    }

    _parseQuote(lines, start) {
        const inner = [];
        let index = start;

        while (index < lines.length) {
            const line = lines[index];
            const match = QUOTE_PATTERN.exec(line);

            if (match) {
                inner.push(match[1]);
                index += 1;
                continue;
            }

            // пустая строка заканчивает цитату
            if (!line.trim()) {
                break;
            }

            // ленивое продолжение цитаты
            inner.push(line);
            index += 1;
        }

        return {
            block: {
                type: BLOCK_QUOTE,
                children: this._parseBlocks(inner),
            },
            nextIndex: index,
        };
    }

    _parseList(lines, start) {
        const first = LIST_ITEM_PATTERN.exec(lines[start]);
        const baseIndent = first[1].length;
        const ordered = /\d/.test(first[2]);
        const startNumber = ordered ? parseInt(first[2], 10) : 1;

        const rawItems = [];
        let current = null;
        let index = start;

        while (index < lines.length) {
            const line = lines[index];

            if (!line.trim()) {
                const next = lines[index + 1] ?? "";

                // пустая строка внутри пункта продолжает его
                if (current && /^\s{2,}\S/.test(next)) {
                    current.lines.push("");
                    index += 1;
                    continue;
                }

                break;
            }

            const match = LIST_ITEM_PATTERN.exec(line);

            if (match && match[1].length === baseIndent) {
                current = {lines: [match[3]]};
                rawItems.push(current);
                index += 1;
                continue;
            }

            // отступ меньше — список закончился
            if (match && match[1].length < baseIndent) {
                break;
            }

            // отступ больше — вложенный пункт текущего
            if (match && match[1].length > baseIndent) {
                if (!current) {
                    break;
                }

                current.lines.push(line.slice(baseIndent + 2));
                index += 1;
                continue;
            }

            if (!current) {
                break;
            }

            // обычный текст — продолжение пункта
            current.lines.push(line.trim());
            index += 1;
        }

        const items = rawItems.map((item) => {
            const blocks = this._parseBlocks(item.lines);
            const firstBlock = blocks[0];

            // простой пункт остаётся абзацем, сложный — набором блоков
            if (blocks.length === 1 && firstBlock.type === BLOCK_PARAGRAPH) {
                return {children: firstBlock.children, blocks: []};
            }

            return {children: [], blocks};
        });

        return {
            block: {
                type: BLOCK_LIST,
                ordered,
                start: startNumber,
                items,
            },
            nextIndex: index,
        };
    }

    _isTableStart(lines, index) {
        const header = lines[index];
        const divider = lines[index + 1];

        if (!header || !divider) {
            return false;
        }

        if (!header.includes("|")) {
            return false;
        }

        return TABLE_DIVIDER_PATTERN.test(divider);
    }

    _parseTable(lines, start) {
        const headerCells = this._splitTableRow(lines[start]);
        const alignments = this._splitTableRow(lines[start + 1]).map(this._parseAlignment);

        const rows = [];
        let index = start + 2;

        while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
            rows.push(this._splitTableRow(lines[index]));
            index += 1;
        }

        const buildRow = (cells) => headerCells.map((_, cellIndex) => ({
            children: parseInline(cells[cellIndex] ?? ""),
            align: alignments[cellIndex] ?? "left",
        }));

        return {
            block: {
                type: BLOCK_TABLE,
                header: buildRow(headerCells),
                rows: rows.map(buildRow),
            },
            nextIndex: index,
        };
    }

    _splitTableRow(line) {
        return line
            .trim()
            .replace(/^\|/, "")
            .replace(/\|$/, "")
            .split("|")
            .map((cell) => cell.trim());
    }

    _parseAlignment(cell) {
        const value = cell.trim();
        const left = value.startsWith(":");
        const right = value.endsWith(":");

        if (left && right) {
            return "center";
        }

        if (right) {
            return "right";
        }

        return "left";
    }

    _parseParagraph(lines, start) {
        const collected = [];
        let index = start;

        while (index < lines.length) {
            const line = lines[index];

            if (!line.trim()) {
                break;
            }

            // следующий блок начинается — абзац закончился
            if (index > start && this._startsBlock(lines, index)) {
                break;
            }

            // подчёркивание заголовка: текст + === или ---
            if (index > start) {
                const setext = SETEXT_PATTERN.exec(line);

                if (setext) {
                    return {
                        block: {
                            type: BLOCK_HEADING,
                            level: setext[1].startsWith("=") ? 1 : 2,
                            children: parseInline(collected.join(" ")),
                        },
                        nextIndex: index + 1,
                    };
                }
            }

            collected.push(line.trim());
            index += 1;
        }

        return {
            block: {
                type: BLOCK_PARAGRAPH,
                children: parseInline(collected.join("\n")),
            },
            nextIndex: index,
        };
    }

    _startsBlock(lines, index) {
        const line = lines[index];

        if (CUSTOM_BLOCK_OPEN_PATTERN.test(line)) {
            return true;
        }

        if (FENCE_PATTERN.test(line)) {
            return true;
        }

        if (HEADING_PATTERN.test(line)) {
            return true;
        }

        if (THEMATIC_BREAK_PATTERN.test(line)) {
            return true;
        }

        if (QUOTE_PATTERN.test(line)) {
            return true;
        }

        if (LIST_ITEM_PATTERN.test(line)) {
            return true;
        }

        if (INDENTED_CODE_PATTERN.test(line)) {
            return true;
        }

        return this._isTableStart(lines, index);
    }
}
