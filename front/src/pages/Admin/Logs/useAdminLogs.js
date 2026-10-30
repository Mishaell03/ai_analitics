import {useCallback, useEffect, useRef, useState} from "react";
import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";
import {appendLogItems} from "@/services/adminLogs.js";

export const EMPTY_FILTERS = {
    user: "", user_id: "", session_id: "", status: "", status_code: "",
    code: "", source: "", date_from: "", date_to: "",
};

export function useAdminLogs(tab) {
    const [filters, setFilters] = useState({...EMPTY_FILTERS});
    const [page, setPage] = useState(1);
    const [result, setResult] = useState({items: [], total: 0, total_pages: 1});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [revision, setRevision] = useState(0);
    const inFlight = useRef(true);

    useEffect(() => {
        const controller = new AbortController();
        inFlight.current = true;
        const fetchLogs = async () => {
            setLoading(true);
            setError(null);
            const params = {page, page_size: 50};
            for (const [key, value] of Object.entries(filters)) {
                if (value !== "") params[key] = typeof value === "string" ? value.trim() : value;
            }
            try {
                const {data} = await api.get(tab === "ai" ? API_ROUTES.ADMIN_AI_LOGS : API_ROUTES.ADMIN_LOGS, {
                    params,
                    signal: controller.signal,
                });
                if (!controller.signal.aborted) {
                    setResult((current) => ({
                        ...data,
                        items: appendLogItems(page === 1 ? [] : current.items, data.items, tab === "ai"),
                    }));
                }
            } catch (requestError) {
                if (!controller.signal.aborted) {
                    setError(requestError.response?.status === 403 ? "forbidden" : "request");
                }
            } finally {
                if (!controller.signal.aborted) {
                    inFlight.current = false;
                    setLoading(false);
                }
            }
        };
        fetchLogs();
        return () => controller.abort();
    }, [tab, filters, page, revision]);

    const applyFilters = (next) => {
        inFlight.current = true;
        setLoading(true);
        setError(null);
        setResult({items: [], total: 0, total_pages: 1});
        setPage(1);
        setFilters(next);
    };

    const hasMore = page < result.total_pages;
    const loadMore = useCallback(() => {
        if (inFlight.current || error || !hasMore) return;
        inFlight.current = true;
        setLoading(true);
        setPage((current) => current + 1);
    }, [error, hasMore]);

    const reload = () => {
        inFlight.current = true;
        setLoading(true);
        setError(null);
        setResult({items: [], total: 0, total_pages: 1});
        setPage(1);
        setRevision((current) => current + 1);
    };

    return {
        ...result, loading, error, applyFilters, reload, hasMore, loadMore,
        retry: () => setRevision((current) => current + 1),
    };
}
