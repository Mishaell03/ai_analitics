import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath, URL } from "node:url";

// В dev браузер и API должны быть на одном origin: backend закрыл CORS
// для localhost, поэтому запросы к /api проксируются на сервер Vite.
const API_PREFIX = "/api";
const DEFAULT_API_TARGET = "http://localhost:8000";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiTarget = env.VITE_API_PROXY_TARGET || DEFAULT_API_TARGET;

  const proxy = {
    [API_PREFIX]: {
      target: apiTarget,
      // Host оставляем фронтенда: backend разрешает localhost-origin
      changeOrigin: false,
    },
  };

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      }
    },
    server: {
      host: true,
      proxy,
    },
    preview: {
      host: true,
      proxy,
    },
  };
})
