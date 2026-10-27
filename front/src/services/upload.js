/**
 * ЗАГРУЗКА MARKDOWN УРОКА В ХРАНИЛИЩЕ
 *
 * Бэкенд выдаёт presigned-ссылку и поля формы: файл отправляется
 * напрямую в MinIO, минуя API. Поэтому здесь нет axios — запрос
 * уходит на чужой домен и не должен слать куки.
 *
 * Поля формы нужно отправить все и обязательно вместе с файлом:
 * политика MinIO проверяет подпись, ключ и тип содержимого.
 *
 * Ошибки сервиса несут код, а не готовый текст: переводит их
 * интерфейс, иначе сообщение осталось бы на одном языке.
 */

const MARKDOWN_CONTENT_TYPE = "text/markdown";

// коды ошибок загрузки
export const UPLOAD_ERROR_CODES = {
    urlMissing: "uploadUrlMissing",
    tooLarge: "uploadFileTooLarge",
    rejected: "uploadRejected",
};

/**
 * Ошибка загрузки с кодом для перевода.
 *
 * @param {string} code код ошибки
 * @param {string} detail техническая деталь
 * @returns {Error}
 */
function uploadError(code, detail) {
    const error = new Error(code);

    error.code = code;
    error.detail = detail;

    return error;
}

/**
 * Загружает Markdown урока по ссылке из бэкенда.
 *
 * @param {object} upload ссылка и поля формы из ответа бэкенда
 * @param {string} upload.url адрес, куда отправляется файл
 * @param {object} upload.fields поля формы политики загрузки
 * @param {number} upload.max_size максимальный размер файла
 * @param {string} content текст урока
 * @param {string} fileName имя файла в хранилище
 * @returns {Promise<boolean>}
 */
export async function uploadLessonMarkdown(upload, content, fileName = "lesson.md") {
    if (!upload?.url) {
        throw uploadError(UPLOAD_ERROR_CODES.urlMissing);
    }

    const size = new Blob([content]).size;

    if (upload.max_size && size > upload.max_size) {
        throw uploadError(UPLOAD_ERROR_CODES.tooLarge, `${size} > ${upload.max_size}`);
    }

    const body = new FormData();

    Object.entries(upload.fields ?? {}).forEach(([key, value]) => {
        body.append(key, value);
    });

    body.append(
        "file",
        new Blob([content], {type: MARKDOWN_CONTENT_TYPE}),
        fileName
    );

    const response = await fetch(upload.url, {
        method: "POST",
        body,
    });

    if (!response.ok) {
        throw uploadError(UPLOAD_ERROR_CODES.rejected, String(response.status));
    }

    return true;
}
