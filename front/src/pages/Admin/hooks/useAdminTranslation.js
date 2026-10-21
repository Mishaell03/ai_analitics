import {useCallback} from "react";
import {getTranslation} from "@/locales/i18n.js";

const LANGUAGE = "ru";

/**
 * Перевод строк админки.
 *
 * Все разделы используют один префикс admin.admin, поэтому хук
 * избавляет от повторения пути и фиксированного языка в каждом
 * компоненте. Функция стабильна между рендерами: её можно безопасно
 * передавать в зависимости useCallback и useEffect.
 */
export function useAdminTranslation() {
    return useCallback(
        (key, params) => getTranslation(`admin.admin.${key}`, LANGUAGE, params),
        []
    );
}
