/**
 * ПРАВИЛА РАБОТЫ С МЕДИАФАЙЛАМИ
 *
 * Файлы живут в приватном хранилище: клиент видит только логический
 * идентификатор и временную ссылку. В Markdown файл вставляется
 * по идентификатору:
 *
 *     ![Описание](asset:m_0123456789abcdef)
 *
 * Ограничения продублированы из конфигурации backend
 * (MEDIA_MAX_IMAGE_SIZE, MEDIA_MAX_VIDEO_SIZE и списки типов):
 * backend остаётся источником истины и отвечает своими ошибками,
 * а эти проверки нужны, чтобы не отправлять заведомо бесперспективный файл.
 */

import {formatBytes} from "./format.js";

const MB = 1024 * 1024;

export const MEDIA_LIMITS = {
    image: {
        maxSize: 10 * MB,
        types: ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"],
        extensions: [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"],
    },
    video: {
        maxSize: 200 * MB,
        types: ["video/mp4"],
        extensions: [".mp4"],
    },
};

// список типов для accept: сначала картинки, потом видео
export const MEDIA_ACCEPT = [
    ...MEDIA_LIMITS.image.types,
    ...MEDIA_LIMITS.video.types,
].join(",");

// только картинки: используется для обложки курса
export const IMAGE_ACCEPT = MEDIA_LIMITS.image.types.join(",");

// максимальный размер Markdown урока.
// Дублирует LESSON_CONTENT_MAX_UPLOAD_SIZE из конфигурации backend:
// точное значение приходит в ответе upload (max_size).
export const LESSON_CONTENT_MAX_SIZE = 512000;

// префикс ссылки на медиафайл в Markdown
export const ASSET_PREFIX = "asset:";

/**
 * Определяет тип файла по расширению и MIME-типу.
 *
 * @param {File} file файл
 * @returns {"image"|"video"|null}
 */
export function getFileKind(file) {
    if (!file) {
        return null;
    }

    const name = (file.name || "").toLowerCase();
    const type = (file.type || "").toLowerCase();

    if (MEDIA_LIMITS.image.types.includes(type)
        || MEDIA_LIMITS.image.extensions.some((extension) => name.endsWith(extension))) {
        return "image";
    }

    if (MEDIA_LIMITS.video.types.includes(type)
        || MEDIA_LIMITS.video.extensions.some((extension) => name.endsWith(extension))) {
        return "video";
    }

    return null;
}

/**
 * Проверяет файл до загрузки.
 *
 * @param {File} file файл
 * @returns {{code: string, params: object}|null} ошибка или null
 */
export function validateMediaFile(file) {
    if (!file) {
        return {code: "mediaFileRequired", params: {}};
    }

    const kind = getFileKind(file);

    if (!kind) {
        return {code: "mediaFileTypeNotAllowed", params: {}};
    }

    if (file.size > MEDIA_LIMITS[kind].maxSize) {
        return {code: "mediaFileTooLarge", params: {limit: formatBytes(MEDIA_LIMITS[kind].maxSize)}};
    }

    return null;
}

/**
 * Идентификатор медиафайла из ссылки вида asset:m_0123456789abcdef.
 *
 * @param {string} source ссылка из Markdown
 * @returns {string|null}
 */
export function parseAssetReference(source) {
    if (!source || !source.startsWith(ASSET_PREFIX)) {
        return null;
    }

    const key = source.slice(ASSET_PREFIX.length);

    // идентификатор генерирует сервер: только буквы, цифры, дефис
    return /^[a-z][a-z0-9_-]{2,63}$/.test(key) ? key : null;
}

/**
 * Markdown-вставка для изображения.
 *
 * @param {object} media файл из списка медиа
 * @param {string} alt подпись
 * @returns {string}
 */
export function buildAssetMarkdown(media, alt) {
    const caption = (alt || media?.original_name || media?.media_key || "").trim();

    return `![${caption}](${ASSET_PREFIX}${media?.media_key ?? ""})`;
}

/**
 * Подпись файла по умолчанию.
 *
 * @param {object} media файл
 * @returns {string}
 */
export function getMediaAlt(media) {
    const name = media?.original_name?.replace(/\.[^.]+$/, "");

    return name || media?.media_key || "";
}

/**
 * Размер файла в человекочитаемом виде: 12,3 КБ.
 *
 * @param {number} value размер в байтах
 * @returns {string}
 */
export {formatBytes} from "./format.js";

/**
 * Длительность видео: 1:05.
 *
 * @param {number} value длительность в секундах
 * @returns {string}
 */
export function formatDuration(value) {
    const seconds = Number(value);

    if (!Number.isFinite(seconds) || seconds <= 0) {
        return "";
    }

    const total = Math.round(seconds);
    const minutes = Math.floor(total / 60);
    const rest = total % 60;

    return `${minutes}:${String(rest).padStart(2, "0")}`;
}
