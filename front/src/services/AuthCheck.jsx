import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

const USER_KEY = "user";
const AUTH_STATUS_KEY = "auth_status";

class AuthCheck {
    static getCachedUser() {
        const cachedUser = localStorage.getItem(USER_KEY);

        if (!cachedUser) {
            return null;
        }

        try {
            const user = JSON.parse(cachedUser);

            if (!this.isSessionValid(user)) {
                this.clear();
                return null;
            }
            return user;
        } catch {
            this.clear();
            return null;
        }
    }

    static isSessionValid(user) {
        if (!user?.expires_at) {
            return false;
        }
        return new Date(user.expires_at) > new Date();
    }

    static isGuest() {
        return localStorage.getItem(AUTH_STATUS_KEY) === "guest";
    }

    static async check() {
        // Есть сохранённый пользователь
        const cachedUser = this.getCachedUser();

        if (cachedUser) {
            return cachedUser;
        }

        if (this.isGuest()) {
            return null;
        }

        try {
            const {data} = await api.get(API_ROUTES.USER_INFO);
            this.save(data);
            localStorage.setItem(AUTH_STATUS_KEY, "auth");
            return data;

        } catch (error) {
            if (error.response?.status === 401) {
                // Запоминаем, что пользователь не авторизован
                localStorage.setItem(AUTH_STATUS_KEY, "guest");
                this.clear();
                return null;
            }
            throw error;
        }
    }

    static clear() {
        localStorage.removeItem(USER_KEY);
    }

    static save(user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        localStorage.setItem(AUTH_STATUS_KEY, "auth");
    }

    static logout() {
        this.clear();

        localStorage.setItem(AUTH_STATUS_KEY, "guest");
    }

    static async refresh() {
        try {
            const { data } = await api.get(API_ROUTES.USER_INFO);

            this.save(data);
            return data;
        } catch (error) {

            if (error.response?.status === 401) {
                this.clear();
                return null;
            }
            throw error;
        }
    }
}

export default AuthCheck;