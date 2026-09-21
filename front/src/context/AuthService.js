import { api } from "@/api/axios.js";
import { API_ROUTES } from "@/api/routes.js";
import ImageCache from "@/context/ImageCache.js";

const USER_KEY = "user";
const AUTH_STATUS_KEY = "auth_status";

// ─────────────────────────────────────────────
// Хранилище — только localStorage
// ─────────────────────────────────────────────

const AuthStorage = {
    getUser() {
        const raw = localStorage.getItem(USER_KEY);
        if (!raw) return null;
        try {
            return JSON.parse(raw);
        } catch {
            this.clearUser();
            return null;
        }
    },

    saveUser(user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        localStorage.setItem(AUTH_STATUS_KEY, "auth");
    },

    clearUser() {
        localStorage.removeItem(USER_KEY);
    },

    markGuest() {
        localStorage.setItem(AUTH_STATUS_KEY, "guest");
    },

    isGuest() {
        return localStorage.getItem(AUTH_STATUS_KEY) === "guest";
    },
};

// ─────────────────────────────────────────────
// Проверка срока сессии
// ─────────────────────────────────────────────

const AuthSession = {
    isValid(user) {
        if (!user?.expires_at) return false;
        return new Date(user.expires_at) > new Date();
    },
};

// ─────────────────────────────────────────────
// Запросы к API
// ─────────────────────────────────────────────

const AuthApi = {
    async getUser() {
        const { data } = await api.get(API_ROUTES.USER_INFO);
        return data;
    },
};

// ─────────────────────────────────────────────
// Основной сервис
// ─────────────────────────────────────────────

/**
 * AuthService
 *
 * check()   — первичная инициализация: localStorage → сессия → API
 * refresh() — принудительный запрос к API (без проверки localStorage)
 * logout()  — очистка всего
 */
const AuthService = {

    /**
     * Получить пользователя при старте приложения.
     *
     * 1. Берём из localStorage
     * 2. Проверяем срок сессии — если валиден, возвращаем
     * 3. Если помечен гостем — возвращаем null без запроса
     * 4. Иначе идём на API
     */
    async check() {
        const cached = AuthStorage.getUser();

        if (cached) {
            if (AuthSession.isValid(cached)) {
                return cached;
            }
            // Сессия протухла — сбрасываем и идём на API
            AuthStorage.clearUser();
        }

        if (AuthStorage.isGuest()) {
            return null;
        }

        return this._fetchAndSave();
    },

    /**
     * Принудительный запрос к API.
     * Используется после логина / смены данных пользователя.
     * Не проверяет localStorage и флаг гостя.
     */
    async refresh() {
        return this._fetchAndSave();
    },

    /**
     * Выход: очищаем хранилище и кэш аватара.
     */
    async logout() {
        AuthStorage.clearUser();
        AuthStorage.markGuest();
        await ImageCache.clear();
    },

    // ── внутренние методы ──────────────────────

    /**
     * Запрос к API → обработка аватара → сохранение.
     * При 401 помечаем гостем и возвращаем null.
     */
    async _fetchAndSave() {
        try {
            const user = await AuthApi.getUser();
            return await this._saveUser(user);
        } catch (error) {
            if (error.response?.status === 401) {
                AuthStorage.clearUser();
                AuthStorage.markGuest();
                return null;
            }
            throw error;
        }
    },

    /**
     * Кэшируем аватар (если есть), убираем оригинальный URL,
     * кладём стабильный ключ кэша и сохраняем в localStorage.
     *
     * Стабильный ключ — pathname без query (например /default-avatars/user6.webp).
     * fetch идёт по полному подписанному URL, в кэш кладём по стабильному ключу.
     */
    async _saveUser(user) {
        let hasImage = false;
        let avatarKey = null;

        if (user.img_url) {
            try {
                avatarKey = new URL(user.img_url).pathname;
            } catch {
                avatarKey = user.img_url;
            }

            hasImage = await ImageCache.save(user.img_url, avatarKey);
        }

        const userToStore = {
            ...user,
            img_url: null,       // оригинальный подписанный URL не храним
            avatar_key: hasImage ? avatarKey : null,
            has_image: hasImage,
        };

        AuthStorage.saveUser(userToStore);
        return userToStore;
    },
};

export default AuthService;