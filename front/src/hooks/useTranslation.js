import {useCallback, useSyncExternalStore} from "react";
import {getLanguage, getTranslation, subscribeLanguage} from "@/locales/i18n.js";

/**
 * Переводы приложения.
 *
 * Хук следит за языком в настройках и перерисовывает компонент,
 * когда язык меняется. Путь ключа задаётся один раз:
 *
 *     const t = useTranslation("courses.course");
 *     t("errorTitle");
 *
 * @param {string} prefix раздел словарей
 * @returns {Function} функция перевода
 */
export function useTranslation(prefix = "") {
    const language = useSyncExternalStore(
        subscribeLanguage,
        getLanguage,
        getLanguage
    );

    return useCallback(
        (key, params) => getTranslation(
            prefix ? `${prefix}.${key}` : key,
            language,
            params
        ),
        [prefix, language]
    );
}
