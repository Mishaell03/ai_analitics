import {useCallback, useEffect, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

const PER_PAGE = 100;

/**
 * Уроки выбранного модуля.
 *
 * Список загружается сам при смене курса или модуля, а операции
 * изменения пробрасывают ошибку наверх — уведомления показывает
 * панель уроков.
 */
export function useModuleLessons(courseSlug, moduleId) {
    const [lessons, setLessons] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [reordering, setReordering] = useState(false);
    const [saving, setSaving] = useState(false);

    const fetchLessons = useCallback(async () => {
        if (!courseSlug || !moduleId) {
            setLessons([]);
            setLoading(false);

            return;
        }

        setError(null);
        setLoading(true);

        try {
            const {data} = await api.get(
                API_ROUTES.ADMIN_COURSE_LESSONS(courseSlug, moduleId),
                {params: {page: 1, page_size: PER_PAGE}}
            );

            setLessons(data.lessons ?? []);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [courseSlug, moduleId]);

    useEffect(() => {
        fetchLessons();
    }, [fetchLessons]);

    // перетаскивание уроков: меняем локальный порядок и сохраняем одним запросом
    const reorderLessons = useCallback(async (reordered) => {
        setLessons(reordered);
        setReordering(true);

        try {
            await api.put(API_ROUTES.ADMIN_COURSE_LESSONS_REORDER(courseSlug, moduleId), {
                lesson_ids: reordered.map((lesson) => lesson.lesson_id),
            });

            await fetchLessons();
        } catch (requestError) {
            // список мог разъехаться — возвращаем как есть на сервере
            await fetchLessons();

            throw requestError;
        } finally {
            setReordering(false);
        }
    }, [courseSlug, moduleId, fetchLessons]);

    // публикация урока: состояние меняется тем же PATCH, что и в редакторе
    const toggleLessonStatus = useCallback(async (lesson) => {
        setSaving(true);

        try {
            await api.patch(
                API_ROUTES.ADMIN_LESSON(courseSlug, moduleId, lesson.lesson_id),
                {is_active: !lesson.is_published}
            );

            await fetchLessons();
        } finally {
            setSaving(false);
        }
    }, [courseSlug, moduleId, fetchLessons]);

    const deleteLesson = useCallback(async (lesson) => {
        setSaving(true);

        try {
            await api.delete(
                API_ROUTES.ADMIN_LESSON(courseSlug, moduleId, lesson.lesson_id)
            );

            await fetchLessons();
        } finally {
            setSaving(false);
        }
    }, [courseSlug, moduleId, fetchLessons]);

    return {
        lessons,
        loading,
        error,
        reordering,
        saving,
        reload: fetchLessons,
        reorderLessons,
        toggleLessonStatus,
        deleteLesson,
    };
}
