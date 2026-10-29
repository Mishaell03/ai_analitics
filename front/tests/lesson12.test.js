import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {test} from "node:test";
import {markdownService} from "../src/services/markdown/MarkdownService.js";
import {buildCodeSolutions} from "../src/services/codeExercises.js";
import {canCompleteLesson} from "../src/services/lessonCompletion.js";

const source = readFileSync(new URL("../../backend/infra/minio/seeds/course-content/1/4/12.md", import.meta.url), "utf8");
const manifest = JSON.parse(readFileSync(new URL("../../backend/docs/lesson-12/solutions.json", import.meta.url), "utf8"));

test("черновик урока 12 не выдаёт фиктивные привязки за существующие ID", () => {
    assert.equal(manifest.status, "draft_unlinked");
    assert.ok(manifest.assignments.every((item) => item.exercise_id === null));
    assert.equal((source.match(/id: none/g) ?? []).length, 3);
});

test("три обязательных SQL-редактора связываются с отдельными эталонами без автопроверки", () => {
    const ids = ["fixture_1", "fixture_2", "fixture_3"]; // только тестовые записи
    let index = 0;
    const linked = source.replaceAll("id: none", () => `id: ${ids[index++]}`);
    const blocks = markdownService.parse(linked).filter((block) => block.blockType === "code");
    assert.deepEqual(blocks.map((block) => block.data.exercise_id), ids);
    assert.ok(blocks.every((block) => block.data.language === "sql" && block.data.valid));
    const drafts = Object.fromEntries(manifest.assignments.map((item, i) => [ids[i], item]));
    const solutions = buildCodeSolutions(linked, drafts);
    assert.deepEqual(solutions.map((item) => item.code), manifest.assignments.map((item) => item.code));
    assert.ok(solutions.every((item) => item.check_mode === "self_review"));
    assert.ok(manifest.assignments.every((item) => !linked.includes(item.code)));
});

test("необязательное id none не блокирует урок и не связано с эталоном", () => {
    const [block] = markdownService.parse(":::code sql\nid: none\n:::");
    assert.equal(block.data.practice, true);
    assert.equal(canCompleteLesson([{type: "code", data: block.data}], {}), true);
    assert.deepEqual(buildCodeSolutions(":::code sql\nid: none\n:::", {}), []);
});

test("самопроверка SQL не подменяет правильные ответы тестов", () => {
    const blocks = [{type: "code", data: {exercise_id: "sql_1"}}, {type: "test", data: {exercise_id: "test_1"}}];
    assert.equal(canCompleteLesson(blocks, {}, ["sql_1", "test_1"]), false);
    assert.equal(canCompleteLesson(blocks, {test_1: {}}, ["sql_1"]), true);
});
