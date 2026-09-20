import axios from "axios";

const _baseConfig = {
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
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