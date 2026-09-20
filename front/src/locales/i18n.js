import ruLogin from "@/locales/auth/login_ru.js";
import ruRegister from "@/locales/auth/register_ru.js";
import ruHome from "@/locales/home/home.js";
import ruError from "@/locales/error/error_ru.js";

const translations = {
    ru: {
        auth: {
            login: ruLogin,
            register: ruRegister,
        },
        home: {
            home: ruHome,
        },
        error: {
            error: ruError,
        }
    },

    en: {
        // Будет позже
    },
};

export function getLanguage() {
    return localStorage.getItem("language") || "ru";
}

export function setLanguage(language) {
    localStorage.setItem("language", language);
}

export function getTranslation(path, language = getLanguage()) {
    const keys = path.split(".");

    let value = translations[language];

    for (const key of keys) {
        value = value?.[key];
    }

    return value ?? path;
}