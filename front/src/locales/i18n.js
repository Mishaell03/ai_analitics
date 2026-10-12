import ruAbout from "@/locales/about/about_ru.js";
import ruLogin from "@/locales/auth/login_ru.js";
import ruRegister from "@/locales/auth/register_ru.js";
import ruСourse from "@/locales/courses/course_ru.js";
import ruСourses from "@/locales/courses/courses_ru.js";
import ruHome from "@/locales/home/home_ru.js";
import ruError from "@/locales/error/error_ru.js";
import ruHeader from "@/locales/layouts/header_ru.js";
import ruProfile from "@/locales/profile/profile_ru.js";
import ruTeachers from "@/locales/teachers/teachers_ru.js";
import ruAdmin from "@/locales/admin/admin_ru.js";

const translations = {
    ru: {
        about: {
            about: ruAbout,
        },
        auth: {
            login: ruLogin,
            register: ruRegister,
        },
        courses: {
            course: ruСourse,
            courses: ruСourses,
        },
        home: {
            home: ruHome,
        },
        profile: {
            profile: ruProfile,
        },
        admin: {
            admin: ruAdmin,
        },
        teachers: {
            teachers: ruTeachers,
        },
        layouts: {
            header: ruHeader,
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