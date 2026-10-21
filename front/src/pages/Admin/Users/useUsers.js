import {useCallback, useEffect, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

// сколько пользователей показываем на странице
export const PER_PAGE = 10;

/**
 * Список пользователей админки.
 *
 * Держит страницу, загружает данные и обновляет строку после
 * блокировки, чтобы статус в таблице совпадал с карточкой.
 */
export function useUsers() {
    const [users, setUsers] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchUsers = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_USERS, {
                params: {
                    page,
                    per_page: PER_PAGE,
                },
            });

            setUsers(data.users ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const goToPreviousPage = useCallback(() => {
        setPage((current) => Math.max(1, current - 1));
    }, []);

    const goToNextPage = useCallback(() => {
        setPage((current) => Math.min(totalPages, current + 1));
    }, [totalPages]);

    const updateUserBlocked = useCallback((userId, isBlocked) => {
        setUsers((current) => current.map((item) =>
            item.user_id === userId
                ? {...item, is_blocked: isBlocked}
                : item
        ));
    }, []);

    return {
        users,
        page,
        totalPages,
        loading,
        error,
        reload: fetchUsers,
        goToPreviousPage,
        goToNextPage,
        updateUserBlocked,
    };
}
