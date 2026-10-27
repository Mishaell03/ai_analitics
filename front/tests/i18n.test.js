import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {test} from "node:test";

import {getLanguage, getTranslation} from "../src/locales/i18n.js";

import ruAbout from "../src/locales/about/about_ru.js";
import ruAdmin from "../src/locales/admin/admin_ru.js";
import ruLogin from "../src/locales/auth/login_ru.js";
import ruRegister from "../src/locales/auth/register_ru.js";
import ruCourse from "../src/locales/courses/course_ru.js";
import ruCourses from "../src/locales/courses/courses_ru.js";
import ruError from "../src/locales/error/error_ru.js";
import ruHeader from "../src/locales/layouts/header_ru.js";
import ruHome from "../src/locales/home/home_ru.js";
import ruProfile from "../src/locales/profile/profile_ru.js";
import ruTeachers from "../src/locales/teachers/teachers_ru.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(here, "..", "src");

// словари приложения: путь в переводах -> словарь
const dictionaries = {
    "teachers.teachers": ruTeachers,
    "about.about": ruAbout,
    "layouts.header": ruHeader,
    "profile.profile": ruProfile,
    "error.error": ruError,
    "auth.register": ruRegister,
    "auth.login": ruLogin,
    "courses.course": ruCourse,
    "courses.courses": ruCourses,
    "home.home": ruHome,
    "admin.admin": ruAdmin,
};

function collectFiles(dir, out = []) {
    for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
        const full = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            collectFiles(full, out);
        } else if (/\.(jsx|js)$/.test(entry.name)) {
            out.push(full);
        }
    }

    return out;
}

/**
 * Значение по пути в словаре.
 */
function resolve(dictionary, key) {
    let value = dictionary;

    for (const part of key.split(".")) {
        if (value === null || value === undefined) {
            return undefined;
        }

        value = value[part];
    }

    return typeof value === "string" ? value : undefined;
}

test("перевод берётся по пути", () => {
    assert.equal(getTranslation("admin.admin.title", "ru"), ruAdmin.title);
    assert.equal(getTranslation("home.home.hero.badge", "ru"), ruHome.hero.badge);
});

test("неизвестный ключ показывает имя ключа, а не путь", () => {
    assert.equal(getTranslation("admin.admin.noSuchKey", "ru"), "noSuchKey");
});

test("незаполненный язык берёт текст языка по умолчанию", () => {
    // переводов на английском ещё нет — интерфейс не должен остаться пустым
    assert.equal(getTranslation("admin.admin.title", "en"), ruAdmin.title);
});

test("параметры подставляются в текст", () => {
    const text = getTranslation("admin.admin.paginationInfo", "ru", {page: 1, total: 3});

    assert.ok(!text.includes("{page}"));
    assert.ok(!text.includes("{total}"));
});

test("неизвестный параметр остаётся в тексте", () => {
    const text = getTranslation("admin.admin.paginationInfo", "ru", {page: 1});

    assert.ok(text.includes("{total}"));
});

test("без настроек язык — русский", () => {
    assert.equal(getLanguage(), "ru");
});

test("во всех словарях ключи на месте", () => {
    const missing = [];

    for (const file of collectFiles(srcDir)) {
        const relative = path.relative(srcDir, file).replace(/\\/g, "/");

        if (relative.startsWith("locales/")) {
            continue;
        }

        const source = fs.readFileSync(file, "utf8");

        // какая функция перевода ведёт в какой словарь
        const helpers = new Map();

        for (const match of source.matchAll(
            /const\s+(\w+)\s*=\s*\(\s*\w+\s*\)\s*=>\s*getTranslation\(\s*`([^`$]+)\$\{key\}`/g
        )) {
            helpers.set(match[1], match[2].replace(/\.$/, ""));
        }

        for (const match of source.matchAll(
            /const\s+(\w+)\s*=\s*useTranslation\(\s*"([^"]+)"\s*\)/g
        )) {
            helpers.set(match[1], match[2]);
        }

        for (const match of source.matchAll(
            /const\s+(\w+)\s*=\s*useAdminTranslation\(\s*\)/g
        )) {
            helpers.set(match[1], "admin.admin");
        }

        for (const [helper, prefix] of helpers) {
            const dictionary = dictionaries[prefix];

            if (!dictionary) {
                missing.push(`${relative}: неизвестный словарь ${prefix}`);
                continue;
            }

            const pattern = new RegExp(`\\b${helper}\\(\\s*["']([^"']+)["']`, "g");

            for (const keyMatch of source.matchAll(pattern)) {
                if (resolve(dictionary, keyMatch[1]) === undefined) {
                    missing.push(`${relative}: ${prefix}.${keyMatch[1]}`);
                }
            }
        }
    }

    assert.deepEqual(missing, []);
});

test("словари оформлены одинаково", () => {
    const localesDir = path.join(srcDir, "locales");
    const problems = [];

    for (const section of fs.readdirSync(localesDir, {withFileTypes: true})) {
        if (!section.isDirectory()) {
            continue;
        }

        const dir = path.join(localesDir, section.name);

        for (const name of fs.readdirSync(dir)) {
            if (!name.endsWith(".js")) {
                continue;
            }

            const source = fs.readFileSync(path.join(dir, name), "utf8");

            // отступ двух пробелов в словарях не используется
            if (/^\s{2}[A-Za-z0-9_]+\s*:/m.test(source)) {
                problems.push(`locales/${section.name}/${name}`);
            }
        }
    }

    assert.deepEqual(problems, []);
});

test("в исходниках нет непереведённого текста", () => {
    const cyrillic = /[Ѐ-ӿ]/;
    const problems = [];

    // убираем комментарии, чтобы не ловить текст в них
    const stripComments = (source) => source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/[^\n]*/g, "");

    for (const file of collectFiles(srcDir)) {
        const relative = path.relative(srcDir, file).replace(/\\/g, "/");

        // в словарях кириллица ожидаема
        if (relative.startsWith("locales/")) {
            continue;
        }

        const source = stripComments(fs.readFileSync(file, "utf8"));

        if (!cyrillic.test(source)) {
            continue;
        }

        source.split("\n").forEach((line, index) => {
            // строковые литералы и текст внутри тегов
            const matches = line.match(/"[^"]*[Ѐ-ӿ][^"]*"|>[^<>{}]*[Ѐ-ӿ][^<>{}]*</g);

            if (matches) {
                problems.push(`${relative}:${index + 1}`);
            }
        });
    }

    assert.deepEqual(problems, []);
});
