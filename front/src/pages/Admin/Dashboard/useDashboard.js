import {useCallback, useEffect, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

// сколько последних пользователей показываем и сколько курсов берём в топ
export const LATEST_USERS = 10;
export const TOP_COURSES = 3;

// пустой ответ, чтобы разметка не зависела от наличия ключей
const EMPTY_DASHBOARD = {
    total_users: 0,
    total_courses: 0,
    total_lessons: 0,
    total_enrollments: 0,
    total_active_sessions: 0,
    latest_users: [],
    top_courses: [],
};

/**
 * Данные дашборда админки.
 *
 * Загружает сводные метрики и преобразует ошибку в состояние страницы:
 * forbidden — нет прав, request — остальные сбои.
 */
export function useDashboard() {
    const [dashboard, setDashboard] = useState(EMPTY_DASHBOARD);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchDashboard = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_DASHBOARD, {
                params: {
                    users: LATEST_USERS,
                    top_courses: TOP_COURSES,
                },
            });

            setDashboard({...EMPTY_DASHBOARD, ...data});
        } catch (requestError) {
            // 403 — сессия есть, но прав администратора нет
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchDashboard();
    }, [fetchDashboard]);

    return {
        dashboard,
        loading,
        error,
        reload: fetchDashboard,
    };
}
