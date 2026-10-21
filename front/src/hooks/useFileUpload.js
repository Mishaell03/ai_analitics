import {useCallback, useEffect, useRef, useState} from "react";

/**
 * ЗАГРУЗКА ФАЙЛА С ПРОГРЕССОМ
 *
 * Общая логика для обложек и медиафайлов:
 *
 *     * один файл нельзя отправить дважды, пока идёт загрузка;
 *     * запрос отменяется, если компонент размонтирован или
 *       пользователь ушёл со страницы;
 *     * ошибка приходит текстом, а не кодом.
 */

/**
 * Текст ошибки из ответа API.
 *
 * Backend отдаёт ошибки в виде {detail: {code, message}},
 * поэтому сообщение забираем оттуда, а при отсутствии — общий текст.
 *
 * @param {Error} requestError ошибка запроса
 * @param {string} fallback текст на случай нестандартного ответа
 * @returns {string}
 */
export function getErrorMessage(requestError, fallback) {
    return requestError?.response?.data?.detail?.message
        || requestError?.message
        || fallback;
}

/**
 * Была ли загрузка отменена.
 *
 * @param {Error} requestError ошибка запроса
 * @returns {boolean}
 */
export function isCanceled(requestError) {
    return requestError?.code === "ERR_CANCELED" || requestError?.name === "CanceledError";
}

export function useFileUpload() {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    const controllerRef = useRef(null);

    // уходим со страницы — запрос отменяется
    useEffect(() => () => {
        controllerRef.current?.abort();
    }, []);

    const cancel = useCallback(() => {
        controllerRef.current?.abort();
        controllerRef.current = null;

        setUploading(false);
        setProgress(0);
    }, []);

    /**
     * Загружает файл.
     *
     * @param {Function} uploader функция загрузки (file, options) => data
     * @param {File} file файл
     * @returns {Promise<object|null>} результат или null при отмене
     */
    const upload = useCallback(async (uploader, file) => {
        if (controllerRef.current) {
            controllerRef.current.abort();
        }

        const controller = new AbortController();

        controllerRef.current = controller;

        setUploading(true);
        setProgress(0);
        setError(null);

        try {
            const result = await uploader(file, {
                onProgress: setProgress,
                signal: controller.signal,
            });

            setProgress(100);

            return result;
        } catch (uploadError) {
            if (isCanceled(uploadError)) {
                return null;
            }

            setError(uploadError);

            return null;
        } finally {
            if (controllerRef.current === controller) {
                controllerRef.current = null;
                setUploading(false);
            }
        }
    }, []);

    return {uploading, progress, error, upload, cancel, setError};
}
