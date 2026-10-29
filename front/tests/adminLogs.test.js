import assert from "node:assert/strict";
import {test} from "node:test";
import {appendLogItems} from "../src/services/adminLogs.js";

test("страницы системной консоли дополняются без потери записей разных источников", () => {
    const first = [{id: 3, source: "event"}, {id: 3, source: "backend"}];
    const next = [{id: 3, source: "backend"}, {id: 2, source: "event"}];
    assert.deepEqual(appendLogItems(first, next, false), [...first, next[1]]);
    assert.equal(first.length, 2);
});

test("пересечения страниц AI-консоли обновляются, а не дублируются", () => {
    const first = [{question_id: 7, status: "pending"}];
    const next = [{question_id: 7, status: "completed"}, {question_id: 6}];
    assert.deepEqual(appendLogItems(first, next, true), next);
    assert.equal(first[0].status, "pending");
});

test("пустая страница не удаляет загруженную историю", () => {
    assert.deepEqual(appendLogItems([{question_id: 1}], [], true), [{question_id: 1}]);
    assert.deepEqual(appendLogItems([], [], false), []);
});
