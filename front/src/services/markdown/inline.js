/**
 * РАЗБОР ИНЛАЙН-РАЗМЕТКИ
 *
 * Результат — дерево узлов, а не HTML: разметку собирает React,
 * поэтому произвольный HTML или скрипт из урока выполниться не может.
 *
 * Поддерживаются: выделение жирным и курсивом, зачёркнутый текст,
 * инлайн-код, ссылки, картинки, автоссылки и экранирование символов.
 */

import {safeUrl} from "./sanitize.js";

const CODE_PATTERN = /(?<ticks>`+)(?<value>[\s\S]*?)\k<ticks>/y;
const IMAGE_PATTERN = /!\[(?<alt>[^\]]*)\]\((?<src>[^()\s]*)(?:\s+"(?<title>[^"]*)")?\)/y;
const LINK_PATTERN = /\[(?<text>[^\]]*)\]\((?<href>[^()\s]*)(?:\s+"(?<title>[^"]*)")?\)/y;
const AUTOLINK_PATTERN = /<((?:https?|mailto):[^>\s]+)>/y;
const STRONG_PATTERN = /(\*\*|__)([\s\S]+?)\1/y;
const STRIKE_PATTERN = /~~([\s\S]+?)~~/y;
const EM_PATTERN = /([*_])([^*\n]+?)\1/y;

// символы, которые можно экранировать обратным слэшем
const ESCAPABLE_PATTERN = /[\\`*_{}[\]()#+\-.!~|>]/;

const NODE_TEXT = "text";
const NODE_CODE = "code";
const NODE_IMAGE = "image";
const NODE_LINK = "link";
const NODE_STRONG = "strong";
const NODE_EMPHASIS = "emphasis";
const NODE_STRIKE = "strikethrough";

function matchAt(pattern, source, index) {
    pattern.lastIndex = index;

    return pattern.exec(source);
}

/**
 * Подчёркивание внутри слова не считается выделением:
 * snake_case не должен превращаться в курсив.
 */
function isWordChar(char) {
    return Boolean(char) && /[\w]/.test(char);
}

function isValidEmphasis(source, index, length, delimiter) {
    if (delimiter !== "_") {
        return true;
    }

    const before = index > 0 ? source[index - 1] : "";
    const after = source[index + length] ?? "";

    return !(isWordChar(before) && isWordChar(after));
}

/**
 * Разбирает инлайн-разметку в дерево узлов.
 *
 * @param {string} source текст без блочной разметки
 * @returns {object[]} узлы разметки
 */
export function parseInline(source) {
    if (!source) {
        return [];
    }

    const nodes = [];
    let buffer = "";
    let index = 0;

    const flush = () => {
        if (buffer) {
            nodes.push({type: NODE_TEXT, value: buffer});
            buffer = "";
        }
    };

    while (index < source.length) {
        const char = source[index];

        // Одиночный Enter — видимый перенос строки (soft break).
        if (char === "\n") {
            flush();
            nodes.push({type: "break"});
            index += 1;
            continue;
        }

        // экранированный символ показываем как обычный
        if (char === "\\" && ESCAPABLE_PATTERN.test(source[index + 1] ?? "")) {
            buffer += source[index + 1];
            index += 2;
            continue;
        }

        if (char === "`") {
            const match = matchAt(CODE_PATTERN, source, index);

            if (match) {
                flush();
                nodes.push({type: NODE_CODE, value: match.groups.value.trim()});
                index += match[0].length;
                continue;
            }
        }

        if (char === "!" && source[index + 1] === "[") {
            const match = matchAt(IMAGE_PATTERN, source, index);

            if (match) {
                flush();
                nodes.push({
                    type: NODE_IMAGE,
                    src: safeUrl(match.groups.src),
                    alt: match.groups.alt ?? "",
                    title: match.groups.title ?? "",
                });
                index += match[0].length;
                continue;
            }
        }

        if (char === "[") {
            const match = matchAt(LINK_PATTERN, source, index);

            if (match) {
                const href = safeUrl(match.groups.href);

                flush();

                if (href) {
                    nodes.push({
                        type: NODE_LINK,
                        href,
                        title: match.groups.title ?? "",
                        children: parseInline(match.groups.text ?? ""),
                    });
                } else {
                    // опасная ссылка остаётся обычным текстом
                    nodes.push({type: NODE_TEXT, value: match.groups.text ?? ""});
                }

                index += match[0].length;
                continue;
            }
        }

        if (char === "<") {
            const match = matchAt(AUTOLINK_PATTERN, source, index);

            if (match) {
                const href = safeUrl(match[1]);

                flush();

                if (href) {
                    nodes.push({
                        type: NODE_LINK,
                        href,
                        title: "",
                        children: [{type: NODE_TEXT, value: match[1]}],
                    });
                } else {
                    nodes.push({type: NODE_TEXT, value: match[0]});
                }

                index += match[0].length;
                continue;
            }
        }

        if (char === "~") {
            const match = matchAt(STRIKE_PATTERN, source, index);

            if (match) {
                flush();
                nodes.push({
                    type: NODE_STRIKE,
                    children: parseInline(match[1]),
                });
                index += match[0].length;
                continue;
            }
        }

        if (char === "*" || char === "_") {
            const strong = matchAt(STRONG_PATTERN, source, index);

            if (strong) {
                flush();
                nodes.push({
                    type: NODE_STRONG,
                    children: parseInline(strong[2]),
                });
                index += strong[0].length;
                continue;
            }

            const emphasis = matchAt(EM_PATTERN, source, index);

            if (emphasis && isValidEmphasis(source, index, emphasis[0].length, emphasis[1])) {
                flush();
                nodes.push({
                    type: NODE_EMPHASIS,
                    children: parseInline(emphasis[2]),
                });
                index += emphasis[0].length;
                continue;
            }
        }

        buffer += char;
        index += 1;
    }

    flush();

    return nodes;
}
