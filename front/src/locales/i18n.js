import ruAbout from "./about/about_ru.js";
import ruLogin from "./auth/login_ru.js";
import ruRegister from "./auth/register_ru.js";
import ruСourse from "./courses/course_ru.js";
import ruСourses from "./courses/courses_ru.js";
import ruHome from "./home/home_ru.js";
import ruError from "./error/error_ru.js";
import ruHeader from "./layouts/header_ru.js";
import ruProfile from "./profile/profile_ru.js";
import ruTeachers from "./teachers/teachers_ru.js";
import ruAdmin from "./admin/admin_ru.js";

// язык по умолчанию: в нём есть все ключи
const DEFAULT_LANGUAGE = "ru";

// событие смены языка: на него подписан хук переводов
const LANGUAGE_EVENT = "app-language-change";

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
        // Будет позже: пока ключи берутся из языка по умолчанию
    },
};

/**
 * Текущий язык приложения.
 *
 * Неизвестный язык игнорируется: иначе интерфейс остался бы без текста.
 *
 * @returns {string}
 */
export function getLanguage() {
    if (typeof localStorage === "undefined") {
        return DEFAULT_LANGUAGE;
    }

    const language = localStorage.getItem("language");

    return language && translations[language] ? language : DEFAULT_LANGUAGE;
}

/**
 * Меняет язык приложения.
 *
 * @param {string} language код языка
 */
export function setLanguage(language) {
    if (!translations[language]) {
        return;
    }

    if (typeof localStorage !== "undefined") {
        localStorage.setItem("language", language);
    }

    if (typeof window !== "undefined") {
        window.dispatchEvent(new Event(LANGUAGE_EVENT));
    }
}

/**
 * Подписка на смену языка.
 *
 * @param {Function} callback обработчик
 * @returns {Function} отписка
 */
export function subscribeLanguage(callback) {
    if (typeof window === "undefined") {
        return () => {};
    }

    window.addEventListener(LANGUAGE_EVENT, callback);

    return () => window.removeEventListener(LANGUAGE_EVENT, callback);
}

/**
 * Значение по пути в словаре.
 *
 * @param {object} dictionary словарь
 * @param {string} path путь ключа
 * @returns {string|undefined}
 */
function resolve(dictionary, path) {
    let value = dictionary;

    for (const key of path.split(".")) {
        if (value === null || value === undefined) {
            return undefined;
        }

        value = value[key];
    }

    return typeof value === "string" ? value : undefined;
}

/**
 * Запасной текст, когда ключа нет ни в одном языке.
 *
 * Показываем имя ключа без пути: «sidebarGroupMain» понятнее,
 * чем «admin.admin.sidebarGroupMain».
 *
 * @param {string} path путь ключа
 * @returns {string}
 */
function fallbackLabel(path) {
    const parts = path.split(".");

    return parts[parts.length - 1];
}

/**
 * Перевод по пути.
 *
 * Ключ ищется в выбранном языке, а если его там нет — в языке
 * по умолчанию: незаполненный перевод не должен оставлять
 * интерфейс без текста.
 *
 * @param {string} path путь ключа
 * @param {string} language язык
 * @param {object} params значения для подстановки
 * @returns {string}
 */
export function getTranslation(path, language = getLanguage(), params) {
    const value = resolve(translations[language], path)
        ?? resolve(translations[DEFAULT_LANGUAGE], path);

    if (typeof value !== "string") {
        return fallbackLabel(path);
    }

    if (!params) {
        return value;
    }

    // подстановка {placeholder} из params
    return value.replace(
        /\{(\w+)}/g,
        (match, key) => (key in params ? String(params[key]) : match)
    );
}
