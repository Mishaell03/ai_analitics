import assert from "node:assert/strict";
import test from "node:test";
import {mergeMentorMessages} from "../src/services/lessonMentor.js";

test("mentor history deduplicates POST results and preserves chronological order", () => {
    const pending = {request_id: "same", question_id: 2, status: "pending"};
    const completed = {...pending, status: "completed", answer: "Text"};
    const older = {request_id: "older", question_id: 1};
    assert.deepEqual(mergeMentorMessages([pending], [older, completed]), [older, completed]);
    assert.equal(pending.status, "pending");
    assert.deepEqual(mergeMentorMessages([completed], [pending]), [completed]);
});

test("mentor keeps only the latest ten requests in the current lesson view", () => {
    const messages = Array.from({length: 15}, (_, index) => ({request_id: String(index), question_id: index}));
    const result = mergeMentorMessages(messages.slice(0, 10), messages.slice(10));
    assert.equal(result.length, 10);
    assert.deepEqual(result.map(item => item.question_id), [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]);
});
