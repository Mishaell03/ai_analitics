import axios from "axios";
import {ROUTES} from "@/router/AppRouter.jsx";

const _baseConfig = {
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
};

const onUnauthorized = (error) => {
    const isLoginPage = window.location.pathname === ROUTES.login;

    if (error.response?.status === 401 && !isLoginPage) {
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