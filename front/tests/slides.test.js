import assert from "node:assert/strict";
import {test} from "node:test";
import {markdownService} from "../src/services/markdown/MarkdownService.js";

test("slides preserves asset image order, alt text and title across paragraphs", () => {
    const [block] = markdownService.parse(':::slides\r\n![Первый](asset:m_first "Обзор")\r\n\r\n![Второй](asset:m_second)\r\n:::');
    assert.equal(block.type, "custom");
    assert.equal(block.blockType, "slides");
    assert.equal(block.implemented, true);
    assert.deepEqual(block.data.slides.map(({src, alt, title}) => ({src, alt, title})), [
        {src: "asset:m_first", alt: "Первый", title: "Обзор"},
        {src: "asset:m_second", alt: "Второй", title: ""},
    ]);
});

test("slides ignores code, ordinary links, unsafe URLs and non-asset images", () => {
    const [block] = markdownService.parse([
        ":::slides",
        "`![inline code](asset:m_code)`",
        "```md", "![fenced code](asset:m_fenced)", "```",
        "[link](asset:m_link)",
        "![external](https://example.com/image.png)",
        "![unsafe](javascript:alert(1))",
        "![invalid](asset:../image.png)",
        "![valid](asset:m_valid)",
        ":::",
    ].join("\n"));
    assert.deepEqual(block.data.slides.map((slide) => slide.src), ["asset:m_valid"]);
});

test("slides can be empty and an unclosed block remains text", () => {
    assert.deepEqual(markdownService.parse(":::slides\n:::")[0].data.slides, []);
    const unclosed = markdownService.parse(":::slides\n![One](asset:m_first)");
    assert.ok(unclosed.every((block) => block.type !== "custom"));
});

test("slides leaves adjacent exercises, unknown blocks and ordinary images intact", () => {
    const blocks = markdownService.parse([
        "![Outside](asset:m_outside)",
        ":::slides", "![Slide](asset:m_first)", ":::",
        ":::code python", "id: example", ":::",
        ":::test", "id: quiz", "Question", "- [ ] One", ":::",
        ":::note", "Note", ":::",
        "After",
    ].join("\n"));
    assert.deepEqual(blocks.map((block) => block.blockType || block.type), [
        "paragraph", "slides", "code", "test", "note", "paragraph",
    ]);
    assert.equal(blocks[0].children[0].src, "asset:m_outside");
    assert.equal(blocks[2].data.exercise_id, "example");
    assert.equal(blocks[2].data.valid, true);
    assert.equal(blocks[3].data.exercise_id, "quiz");
    assert.equal(blocks[4].implemented, false);
});
