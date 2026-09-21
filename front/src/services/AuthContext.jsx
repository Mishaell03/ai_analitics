import {createContext, useContext, useEffect, useRef, useState} from "react";
import AuthCheck from "@/services/AuthCheck.jsx";

const AuthContext = createContext(null);

export function AuthProvider({children}) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const initialized = useRef(false);

    useEffect(() => {

        if (initialized.current) {
            return;
        }

        initialized.current = true;

        async function initAuth() {
            console.log("AuthProvider checked");

            const user = await AuthCheck.check();

            setUser(user);
            setLoading(false);
        }

        initAuth();

    }, []);


    return (
        <AuthContext.Provider
            value={{
                user,
                loading,

                setUser: (user) => {
                    AuthCheck.save(user);
                    setUser(user);
                },

                logout: () => {
                    AuthCheck.clear();
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