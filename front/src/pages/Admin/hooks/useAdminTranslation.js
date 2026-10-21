import {useTranslation} from "@/hooks/useTranslation.js";

/**
 * Перевод строк админки.
 *
 * Все разделы используют один префикс admin.admin, поэтому хук
 * избавляет от повторения пути. Функция стабильна между рендерами:
 * её можно безопасно передавать в зависимости useCallback и useEffect.
 *
 * @returns {Function} функция перевода
 */
export function useAdminTranslation() {
    return useTranslation("admin.admin");
}
