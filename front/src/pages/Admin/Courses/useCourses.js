import {useCallback, useEffect, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

// сколько курсов показываем на странице
export const PER_PAGE = 10;

/**
 * Курсы админки: список, страницы и операции изменения.
 *
 * Методы изменения пробрасывают ошибку наверх: текст сообщения
 * и уведомление — задача страницы.
 */
export function useCourses() {
    const [courses, setCourses] = useState([]);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);

    const fetchCourses = useCallback(async () => {
        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_COURSES, {
                params: {page, page_size: PER_PAGE},
            });

            setCourses(data.courses ?? []);
            setTotalPages(data.total_pages ?? 1);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [page]);

    useEffect(() => {
        fetchCourses();
    }, [fetchCourses]);

    const goToPreviousPage = useCallback(() => {
        setPage((current) => Math.max(1, current - 1));
    }, []);

    const goToNextPage = useCallback(() => {
        setPage((current) => Math.min(totalPages, current + 1));
    }, [totalPages]);

    const runMutation = useCallback(async (request) => {
        setSaving(true);

        try {
            const result = await request();

            await fetchCourses();

            return result;
        } finally {
            setSaving(false);
        }
    }, [fetchCourses]);

    // создание и изменение возвращают сохранённый курс: обложку
    // отправляют уже на его slug, а не на значение из формы
    const createCourse = useCallback(
        async (payload) => {
            const {data} = await runMutation(
                () => api.post(API_ROUTES.ADMIN_COURSES, payload)
            );

            return data;
        },
        [runMutation]
    );

    const updateCourse = useCallback(
        async (originalSlug, payload) => {
            const {data} = await runMutation(
                () => api.patch(API_ROUTES.ADMIN_COURSE_BY_ID(originalSlug), payload)
            );

            return data;
        },
        [runMutation]
    );

    const deleteCourse = useCallback(
        (course) => runMutation(() => api.delete(API_ROUTES.ADMIN_COURSE_BY_ID(course.slug))),
        [runMutation]
    );

    const toggleCourseStatus = useCallback(
        (course) => runMutation(() => api.post(
            course.is_active
                ? API_ROUTES.ADMIN_COURSE_DEACTIVATE(course.slug)
                : API_ROUTES.ADMIN_COURSE_ACTIVATE(course.slug)
        )),
        [runMutation]
    );

    return {
        courses,
        page,
        totalPages,
        loading,
        error,
        saving,
        reload: fetchCourses,
        goToPreviousPage,
        goToNextPage,
        createCourse,
        updateCourse,
        deleteCourse,
        toggleCourseStatus,
    };
}
