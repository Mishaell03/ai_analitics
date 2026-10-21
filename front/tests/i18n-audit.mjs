import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(here, "..", "src");

function collect(dir, out = []) {
    for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
        const full = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            collect(full, out);
        } else if (/\.(jsx|js)$/.test(entry.name)) {
            out.push(full);
        }
    }

    return out;
}

const dictionaryFiles = {
    "teachers.teachers": "locales/teachers/teachers_ru.js",
    "about.about": "locales/about/about_ru.js",
    "layouts.header": "locales/layouts/header_ru.js",
    "profile.profile": "locales/profile/profile_ru.js",
    "error.error": "locales/error/error_ru.js",
    "auth.register": "locales/auth/register_ru.js",
    "auth.login": "locales/auth/login_ru.js",
    "courses.course": "locales/courses/course_ru.js",
    "courses.courses": "locales/courses/courses_ru.js",
    "home.home": "locales/home/home_ru.js",
    "admin.admin": "locales/admin/admin_ru.js",
};

function flatten(dictionary, prefix = "") {
    const result = [];

    for (const [key, value] of Object.entries(dictionary)) {
        const full = prefix ? `${prefix}.${key}` : key;

        if (typeof value === "string") {
            result.push(full);
        } else if (value && typeof value === "object") {
            result.push(...flatten(value, full));
        }
    }

    return result;
}

const sources = collect(srcDir)
    .filter((file) => !file.includes(`${path.sep}locales${path.sep}`))
    .map((file) => fs.readFileSync(file, "utf8"))
    .join("\n");

for (const [prefix, file] of Object.entries(dictionaryFiles)) {
    const dictionary = (await import(pathToFileURL(path.join(here, "..", "src", file)))).default;
    const unused = flatten(dictionary).filter((key) => {
        const leaf = key.split(".").pop();

        return !new RegExp(`["'\`]${leaf.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["'\`]`).test(sources);
    });

    console.log(`${prefix}: не используются ${unused.length}`);
    if (unused.length) {
        console.log("  " + unused.join(", "));
    }
}
