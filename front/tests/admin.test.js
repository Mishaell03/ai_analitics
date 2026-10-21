import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {test} from "node:test";

import {getModuleId} from "../src/pages/Admin/utils/getModuleId.js";

/**
 * Проверки админки.
 *
 * Здесь нет React: проверяются чистые правила, которые легко
 * нарушить незаметно — ключи переводов и разметка скелетонов.
 */

const here = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(here, "..", "src");
const adminDir = path.join(srcDir, "pages", "Admin");
const localeFile = path.join(srcDir, "locales", "admin", "admin_ru.js");

const CYRILLIC = /[Ѐ-ӿ]/;

/**
 * Все файлы папки (рекурсивно).
 */
function collectFiles(dir, out = []) {
    for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
        const full = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            collectFiles(full, out);
        } else {
            out.push(full);
        }
    }

    return out;
}

/**
 * Убирает комментарии, чтобы проверка текста их не задевала.
 */
function stripComments(source) {
    return source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/[^\n]*/g, "");
}

const adminFiles = collectFiles(adminDir);
const sourceFiles = adminFiles.filter((file) => /\.(jsx|js)$/.test(file));
const cssFiles = adminFiles.filter((file) => file.endsWith(".css"));

test("идентификатор модуля берётся из module_id или id", () => {
    assert.equal(getModuleId({module_id: 7, id: 7}), 7);
    assert.equal(getModuleId({id: 9}), 9);
    assert.equal(getModuleId({module_id: null, id: 4}), 4);
    assert.equal(getModuleId({}), null);
    assert.equal(getModuleId(null), null);
    assert.equal(getModuleId(undefined), null);
});

test("в админке нет забытых ключей перевода", () => {
    const locale = fs.readFileSync(localeFile, "utf8");
    const keys = new Set();

    for (const match of locale.matchAll(/^\s{4}([A-Za-z0-9_]+)\s*:/gm)) {
        keys.add(match[1]);
    }

    const missing = [];

    for (const file of sourceFiles) {
        const source = fs.readFileSync(file, "utf8");

        for (const match of source.matchAll(/\bt\(\s*["']([A-Za-z0-9_]+)["']/g)) {
            if (!keys.has(match[1])) {
                missing.push(`${path.relative(adminDir, file)}: ${match[1]}`);
            }
        }
    }

    assert.deepEqual(missing, []);
});

test("в админке нет текста, который не прошёл через переводы", () => {
    const offenders = [];

    for (const file of sourceFiles) {
        const source = stripComments(fs.readFileSync(file, "utf8"));
        const lines = source.split("\n");

        lines.forEach((line, index) => {
            // строковые литералы и текст внутри тегов
            const matches = line.match(
                /"[^"]*[Ѐ-ӿ][^"]*"|>[^<>{}]*[Ѐ-ӿ][^<>{}]*</g
            );

            if (matches) {
                offenders.push(`${path.relative(adminDir, file)}:${index + 1}`);
            }
        });
    }

    assert.deepEqual(offenders, []);
});

test("значения data-width из разметки есть в стилях", () => {
    const styles = cssFiles.map((file) => fs.readFileSync(file, "utf8")).join("\n");

    const missing = [];

    for (const file of sourceFiles) {
        const source = fs.readFileSync(file, "utf8");

        for (const match of source.matchAll(/data-width="([^"]+)"/g)) {
            const selector = `[data-width="${match[1]}"]`;

            if (!styles.includes(selector)) {
                missing.push(`${path.relative(adminDir, file)}: ${match[1]}`);
            }
        }
    }

    assert.deepEqual(missing, []);
});

test("в админке нет кириллицы вне переводов и комментариев", () => {
    // проверка на файлах-стилях: в CSS кириллица недопустима
    const offenders = [];

    for (const file of cssFiles) {
        const source = stripComments(fs.readFileSync(file, "utf8"));

        if (CYRILLIC.test(source)) {
            offenders.push(path.relative(adminDir, file));
        }
    }

    assert.deepEqual(offenders, []);
});
