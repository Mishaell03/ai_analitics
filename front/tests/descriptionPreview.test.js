import assert from "node:assert/strict";
import {test} from "node:test";
import {descriptionPreview} from "../src/services/descriptionPreview.js";

function text(nodes) {
    return nodes.map((node) => node.children ? text(node.children) : node.value).join("");
}

test("превью содержит только первый абзац", () => {
    assert.equal(text(descriptionPreview("Первый\n\nВторой")), "Первый…");
});

test("превью ограничивает видимые символы, сохраняя жирное выделение", () => {
    const nodes = descriptionPreview(`**${"а".repeat(210)}**`);
    assert.equal(text(nodes), `${"а".repeat(200)}…`);
    assert.equal(nodes[0].type, "strong");
});

test("короткий абзац не получает троеточие", () => {
    assert.equal(text(descriptionPreview("Короткое **описание**")), "Короткое описание");
});
