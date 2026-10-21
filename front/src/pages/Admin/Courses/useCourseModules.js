import {useCallback, useEffect, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {getModuleId} from "@/pages/Admin/utils/getModuleId.js";

const PER_PAGE = 100;

/**
 * Модули выбранного курса.
 *
 * При смене курса список очищается сразу, чтобы на экране не остались
 * уроки и действия от предыдущего курса.
 */
export function useCourseModules(courseSlug) {
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [reordering, setReordering] = useState(false);
    const [saving, setSaving] = useState(false);

    const fetchModules = useCallback(async () => {
        setError(null);

        if (!courseSlug) {
            setModules([]);
            setLoading(false);

            return;
        }

        setLoading(true);

        // список очищаем сразу: пока грузятся модули другого курса,
        // нельзя показывать уроки от старого
        setModules([]);

        try {
            const {data} = await api.get(API_ROUTES.ADMIN_COURSE_MODULES(courseSlug), {
                params: {page: 1, page_size: PER_PAGE},
            });

            setModules(data.modules ?? []);
        } catch (requestError) {
            setError(requestError.response?.status === 403 ? "forbidden" : "request");
        } finally {
            setLoading(false);
        }
    }, [courseSlug]);

    useEffect(() => {
        fetchModules();
    }, [fetchModules]);

    const runMutation = useCallback(async (request) => {
        setSaving(true);

        try {
            await request();
            await fetchModules();
        } finally {
            setSaving(false);
        }
    }, [fetchModules]);

    const createModule = useCallback(
        (payload) => runMutation(
            () => api.post(API_ROUTES.ADMIN_COURSE_MODULES(courseSlug), payload)
        ),
        [courseSlug, runMutation]
    );

    const updateModule = useCallback(
        (moduleId, payload) => runMutation(
            () => api.patch(API_ROUTES.ADMIN_MODULE_BY_ID(moduleId), payload)
        ),
        [runMutation]
    );

    const deleteModule = useCallback(
        (module) => runMutation(
            () => api.delete(API_ROUTES.ADMIN_MODULE_BY_ID(getModuleId(module)))
        ),
        [runMutation]
    );

    const toggleModuleStatus = useCallback(
        (module) => runMutation(() => api.post(
            module.is_active
                ? API_ROUTES.ADMIN_MODULE_DEACTIVATE(getModuleId(module))
                : API_ROUTES.ADMIN_MODULE_ACTIVATE(getModuleId(module))
        )),
        [runMutation]
    );

    // перетаскивание модулей: меняем локальный порядок и сохраняем одним запросом
    const reorderModules = useCallback(async (reordered) => {
        setModules(reordered);
        setReordering(true);

        try {
            await api.put(API_ROUTES.ADMIN_COURSE_MODULES_REORDER(courseSlug), {
                module_ids: reordered.map(getModuleId),
            });

            await fetchModules();
        } catch (requestError) {
            // список мог разъехаться — возвращаем как есть на сервере
            await fetchModules();

            throw requestError;
        } finally {
            setReordering(false);
        }
    }, [courseSlug, fetchModules]);

    return {
        modules,
        loading,
        error,
        reordering,
        saving,
        reload: fetchModules,
        createModule,
        updateModule,
        deleteModule,
        toggleModuleStatus,
        reorderModules,
    };
}
