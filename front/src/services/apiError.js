/**
 * Текст ошибки из ответа API.
 *
 * Backend отдаёт ошибки в виде {detail: {code, message, error}},
 * поэтому для пользователя берём message, затем error, а при
 * отсутствии — заранее подготовленный текст.
 *
 * @param {Error} requestError ошибка запроса
 * @param {string} fallback текст на случай нестандартного ответа
 * @returns {string}
 */
export function getApiErrorMessage(requestError, fallback) {
    const detail = requestError?.response?.data?.detail;

    return detail?.message || detail?.error || fallback;
}
