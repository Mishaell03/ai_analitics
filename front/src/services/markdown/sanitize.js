/**
 * ПРОВЕРКА БЕЗОПАСНОСТИ ССЫЛОК
 *
 * Markdown урока приходит из хранилища, поэтому ссылку из него
 * нельзя отдавать в разметку как есть: протокол javascript: выполнит
 * код, а data: спрячет внутри себя картинку с кодом.
 *
 * Разрешены только http, https, mailto, tel и относительные пути.
 */

const SAFE_SCHEMES = new Set(["http:", "https:", "mailto:", "tel:"]);

// схема в начале адреса: protocol://host или protocol:
const SCHEME_PATTERN = /^([a-zA-Z][a-zA-Z0-9+.-]*):/;

// управляющие символы браузер вырезает из адреса сам,
// поэтому их нужно убрать до проверки схемы
// eslint-disable-next-line no-control-regex
const CONTROL_CHARS_PATTERN = /[\u0000-\u001F\u007F]/g;

/**
 * Безопасна ли ссылка.
 *
 * @param {string} url адрес из Markdown
 * @returns {boolean}
 */
export function isSafeUrl(url) {
    if (!url) {
        return false;
    }

    const value = url.trim();

    if (!value) {
        return false;
    }

    // протокол-относительный адрес ведёт на чужой домен
    if (value.startsWith("//")) {
        return false;
    }

    const cleaned = value.replace(CONTROL_CHARS_PATTERN, "");

    const match = SCHEME_PATTERN.exec(cleaned);

    // адрес без схемы — относительный, он остаётся на сайте
    if (!match) {
        return true;
    }

    return SAFE_SCHEMES.has(`${match[1].toLowerCase()}:`);
}

/**
 * Безопасный адрес или null, если ссылку показывать нельзя.
 *
 * @param {string} url адрес из Markdown
 * @returns {string|null}
 */
export function safeUrl(url) {
    return isSafeUrl(url) ? url.trim() : null;
}

/**
 * Является ли адрес ссылкой на медиафайл урока.
 *
 * Медиафайлы лежат в хранилище и отдаются по короткой ссылке,
 * поэтому абсолютный адрес файла — это уже готовая ссылка.
 *
 * @param {string} url адрес из Markdown
 * @returns {boolean}
 */
export function isMediaUrl(url) {
    if (!url) {
        return false;
    }

    return /^(https?:)?\/\//i.test(url.trim()) || url.trim().startsWith("/");
}
