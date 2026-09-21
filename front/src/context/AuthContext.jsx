import { createContext, useContext, useEffect, useRef, useState } from "react";
import AuthService from "@/context/AuthService.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const initialized = useRef(false);

    useEffect(() => {
        if (initialized.current) return;
        initialized.current = true;

        AuthService.check()
            .then(setUser)
            .finally(() => setLoading(false));
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,

                // Вызывай после логина: AuthService.refresh() уже вызван снаружи,
                // просто передай сюда полученного пользователя.
                setUser,

                // Принудительно обновить с сервера (например после смены профиля).
                refresh: async () => {
                    const updated = await AuthService.refresh();
                    setUser(updated);
                    return updated;
                },

                logout: async () => {
                    await AuthService.logout();
                    setUser(null);
                },
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}