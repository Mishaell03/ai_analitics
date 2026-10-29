import assert from "node:assert/strict";
import {test} from "node:test";
import {canCompleteLesson, isLessonBrowsingAllowed} from "../src/services/lessonCompletion.js";

const blocks = [
    {type: "test", data: {exercise_id: "test-1"}},
    {type: "code", data: {exercise_id: "code-1"}},
    {type: "video", data: {exercise_id: "video-1"}},
    {type: "test", data: {exercise_id: null}},
];

test("завершение всегда требует пройти тесты и задания с кодом", () => {
    assert.equal(canCompleteLesson(blocks, {}), false);
    assert.equal(canCompleteLesson(blocks, {"test-1": {}}), false);
    assert.equal(canCompleteLesson(blocks, {"test-1": {}, "code-1": {}}), true);
});

test("урок без заданий можно завершить при включённой проверке", () => {
    assert.equal(canCompleteLesson([], {}), true);
});

test("просмотр включается только с разрешением бэка и фронта", () => {
    for (const value of ["true", "TRUE", " true "]) {
        assert.equal(isLessonBrowsingAllowed(value, true), true);
        assert.equal(isLessonBrowsingAllowed(value, false), false);
        assert.equal(isLessonBrowsingAllowed(value, undefined), false);
    }
    for (const value of ["false", undefined, "", "invalid"]) {
        assert.equal(isLessonBrowsingAllowed(value, true), false);
    }
});

test("свободный просмотр не засчитывает задания и не разрешает завершение", () => {
    const completed = {};
    assert.equal(isLessonBrowsingAllowed("true", true), true);
    assert.equal(canCompleteLesson(blocks, completed), false);
    assert.deepEqual(completed, {});
});
