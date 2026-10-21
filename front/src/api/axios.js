import axios from "axios";
import {ROUTES} from "@/router/AppRouter.jsx";
import {API_ROUTES} from "@/api/routes.js";

const _baseConfig = {
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
};

const AUTH_PAGES = new Set([ROUTES.login, ROUTES.registration]);

const onUnauthorized = (error) => {
    const isAuthPage = AUTH_PAGES.has(window.location.pathname);

    // GET /me — это фоновая проверка сессии. Для гостя 401 здесь
    // ожидаем: редирект не должен выкидывать его с регистрации
    // или публичной страницы.
    const isGuestSessionCheck =
        error.config?.method === "get" &&
        error.config?.url === API_ROUTES.USER_INFO;

    if (error.response?.status === 401 && !isAuthPage && !isGuestSessionCheck) {
        window.location.assign(ROUTES.login);
    }

    return Promise.reject(error);
};

// JSON
export const api = axios.create({
    ..._baseConfig,
    headers: {
        "Content-Type": "application/json",
    },
});

// FormData
export const formApi = axios.create({
    ..._baseConfig,
});

api.interceptors.response.use((response) => response, onUnauthorized);
formApi.interceptors.response.use((response) => response, onUnauthorized);