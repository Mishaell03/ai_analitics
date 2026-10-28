import assert from "node:assert/strict";
import test from "node:test";
import {buildCodeSolutions, ensureCodeExerciseIds, parseCodeExercises} from "../src/services/codeExercises.js";
import {MarkdownService} from "../src/services/markdown/MarkdownService.js";

test("code IDs are generated once and survive edits/reordering", () => {
    const source = ensureCodeExerciseIds(":::code python\n:::\n\n:::code sql\n:::");
    assert.equal(ensureCodeExerciseIds(source), source);
    const blocks = parseCodeExercises(source);
    assert.equal(blocks.length, 2);
    assert.notEqual(blocks[0].exercise_id, blocks[1].exercise_id);
    const drafts = Object.fromEntries(blocks.map((block) => [block.exercise_id,
        {language: block.language, code: "SECRET_REFERENCE"}]));
    const solutions = buildCodeSolutions(source, drafts);
    assert.equal(solutions.length, 2);
    assert.ok(!source.includes("SECRET_REFERENCE"));
    assert.deepEqual(buildCodeSolutions("", drafts), []);
});

test("fenced directive examples remain examples", () => {
    const source = "```markdown\n:::code python\n:::\n```";
    assert.equal(ensureCodeExerciseIds(source), source);
    assert.equal(parseCodeExercises(source).length, 0);
});

test("missing, duplicate and mismatched references fail closed", () => {
    const source = ":::code python\nid: a\n:::";
    assert.throws(() => buildCodeSolutions(source, {}));
    assert.throws(() => buildCodeSolutions(source, {a: {language: "sql", code: "SELECT 1"}}));
    assert.throws(() => buildCodeSolutions(`${source}\n${source}`, {a: {language: "python", code: "pass"}}));
    assert.throws(() => buildCodeSolutions(":::code ruby\nid: a\n:::", {}));
    assert.throws(() => buildCodeSolutions(":::code python\nid: a\nprint(42)\n:::", {}));
});

test("renderer parser recognizes both languages without reference code", () => {
    for (const language of ["sql", "python"]) {
        const [block] = new MarkdownService().parse(`:::code ${language}\nid: stable\n:::`);
        assert.equal(block.blockType, "code");
        assert.deepEqual(block.data, {exercise_id: "stable", language, valid: true});
    }
});
