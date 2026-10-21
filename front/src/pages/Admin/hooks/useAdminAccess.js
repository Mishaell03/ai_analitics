import {useAuth} from "@/context/AuthContext.jsx";

/**
 * Доступ к разделу админки.
 *
 * Запрет приходит из двух мест: backend отвечает 403, либо у текущего
 * пользователя нет прав администратора. Проверка собрана в одном месте,
 * чтобы страницы не повторяли её по-разному.
 *
 * @param {string|null|undefined} requestError состояние ошибки запроса
 * @returns {{authLoading: boolean, isForbidden: boolean}}
 */
export function useAdminAccess(requestError) {
    const {user, loading: authLoading} = useAuth();

    return {
        authLoading,
        isForbidden: requestError === "forbidden"
            || (!authLoading && !user?.is_admin),
    };
}
