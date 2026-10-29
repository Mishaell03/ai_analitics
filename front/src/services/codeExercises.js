import {generateExerciseId} from "./exercises.js";

// Только верхнеуровневые директивы; примеры внутри fenced code не меняются.
export function parseCodeExercises(source) {
    const lines = (source ?? "").replace(/\r\n?/g, "\n").split("\n");
    const blocks = [];
    let fence = null;
    for (let index = 0; index < lines.length; index += 1) {
        const marker = /^ {0,3}(`{3,}|~{3,})/.exec(lines[index]);
        if (marker) {
            if (!fence) fence = marker[1];
            else if (marker[1][0] === fence[0] && marker[1].length >= fence.length) fence = null;
            continue;
        }
        if (fence) continue;
        const match = /^:::\s*code[ \t]+(\S+)[ \t]*$/.exec(lines[index]);
        if (!match) continue;
        const start = index;
        while (index + 1 < lines.length && !/^:::\s*$/.test(lines[index + 1])) index += 1;
        const body = lines.slice(start + 1, index + 1);
        const id = /^id:\s*([A-Za-z0-9_-]{1,64})\s*$/i.exec(body[0] ?? "")?.[1] ?? "";
        blocks.push({language: match[1], exercise_id: id, start, end: index + 1,
            valid: index + 1 < lines.length && (body.every((line) => !line.trim())
                || (id && body.slice(1).every((line) => !line.trim())))});
        index += 1;
    }
    return blocks;
}

export function ensureCodeExerciseIds(source) {
    const lines = (source ?? "").replace(/\r\n?/g, "\n").split("\n");
    for (const block of parseCodeExercises(source).reverse()) {
        if (!block.exercise_id && block.valid && !/^:::[ \t]+code/.test(lines[block.start])) {
            lines.splice(block.start + 1, 0, `id: ${generateExerciseId()}`);
        }
    }
    return lines.join("\n");
}

export function buildCodeSolutions(content, drafts) {
    const lines = (content ?? "").replace(/\r\n?/g, "\n").split("\n");
    const blocks = parseCodeExercises(content).filter((block) =>
        !(block.valid && block.exercise_id === "none") && (block.exercise_id || !block.valid
            || !/^:::[ \t]+code/.test(lines[block.start])));
    const ids = new Set();
    return blocks.map((block) => {
        const draft = drafts[block.exercise_id];
        if (!block.valid || !["sql", "python"].includes(block.language)
            || !block.exercise_id || block.exercise_id === "reference" || ids.has(block.exercise_id)
            || !draft?.code?.trim() || draft.language !== block.language) {
            throw new Error("Invalid code block or missing reference solution");
        }
        ids.add(block.exercise_id);
        return {exercise_id: block.exercise_id, language: block.language, code: draft.code};
    });
}
