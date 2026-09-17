import axios from "axios";

const _baseConfig = {
    baseURL: import.meta.env.VITE_API_URL,
};

const _addAuthInterceptor = (config) => {
    const sessionToken = localStorage.getItem("session_token");

    if (sessionToken) {
        config.headers.Authorization = `Bearer ${sessionToken}`;
    }

    return config;
};


// api with auth and without
export const api = axios.create({
    ..._baseConfig,
    headers: {
        "Content-Type": "application/json",
    },
});

// FormData always with auth
export const formApi = axios.create({
    ..._baseConfig,
});

api.interceptors.request.use(_addAuthInterceptor);
formApi.interceptors.request.use(_addAuthInterceptor);