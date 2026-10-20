/**
 * ЗАГРУЗКА MARKDOWN УРОКА В ХРАНИЛИЩЕ
 *
 * Бэкенд выдаёт presigned-ссылку и поля формы: файл отправляется
 * напрямую в MinIO, минуя API. Поэтому здесь нет axios — запрос
 * уходит на чужой домен и не должен слать куки.
 *
 * Поля формы нужно отправить все и обязательно вместе с файлом:
 * политика MinIO проверяет подпись, ключ и тип содержимого.
 */

const MARKDOWN_CONTENT_TYPE = "text/markdown";

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
        throw new Error("Ссылка на загрузку не получена");
    }

    const size = new Blob([content]).size;

    if (upload.max_size && size > upload.max_size) {
        throw new Error("Файл больше, чем принимает хранилище");
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
        throw new Error(`Хранилище отклонило файл: ${response.status}`);
    }

    return true;
}
