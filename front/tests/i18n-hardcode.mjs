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
        } else if (/\.(jsx?|js)$/.test(entry.name)) {
            out.push(full);
        }
    }

    return out;
}

// убираем комментарии, чтобы не ловить текст в них
function stripComments(source) {
    return source
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/\/\/[^\n]*/g, "");
}

const CYRILLIC = /[Ѐ-ӿ]/;

for (const file of collect(srcDir)) {
    const relative = path.relative(srcDir, file).replace(/\\/g, "/");

    // словари и тесты — там кириллица ожидаема
    if (relative.startsWith("locales/") || relative.startsWith("tests/")) {
        continue;
    }

    const source = stripComments(fs.readFileSync(file, "utf8"));

    if (!CYRILLIC.test(source)) {
        continue;
    }

    const lines = source.split("\n");
    const hits = [];

    lines.forEach((line, index) => {
        const matches = line.match(
            /"[^"]*[Ѐ-ӿ][^"]*"|>[^<>{}]*[Ѐ-ӿ][^<>{}]*</g
        );

        if (matches) {
            hits.push(`  ${index + 1}: ${line.trim().slice(0, 110)}`);
        }
    });

    if (hits.length) {
        console.log(relative);
        console.log(hits.join("\n"));
    }
}
