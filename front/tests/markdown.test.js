import assert from "node:assert/strict";
import {test} from "node:test";

import {
    CustomBlockHandler,
    MarkdownService,
    markdownService,
} from "../src/services/markdown/MarkdownService.js";
import {isSafeUrl} from "../src/services/markdown/sanitize.js";

function parse(source) {
    return markdownService.parse(source);
}

function findBlock(blocks, type) {
    return blocks.find((block) => block.type === type);
}

test("заголовки разбираются по уровням", () => {
    const blocks = parse("# Первый\n\n## Второй\n\n### Третий\n");

    assert.deepEqual(
        blocks.map((block) => [block.type, block.level]),
        [
            ["heading", 1],
            ["heading", 2],
            ["heading", 3],
        ],
    );
});

test("абзац собирает текст до пустой строки", () => {
    const blocks = parse("Первая строка\nвторая строка\n\nДругой абзац\n");

    assert.equal(blocks.length, 2);
    assert.equal(blocks[0].type, "paragraph");
    assert.equal(blocks[0].children[0].value, "Первая строка\nвторая строка");
});

test("инлайн-разметка разбирается в узлы", () => {
    const blocks = parse("Обычный **жирный** и *курсив* и `код`\n");

    const types = blocks[0].children.map((node) => node.type);

    assert.deepEqual(types, ["text", "strong", "text", "emphasis", "text", "code"]);
});

test("незакрытое выделение остаётся текстом", () => {
    const blocks = parse("Текст **без закрытия\n");

    assert.equal(blocks[0].children.length, 1);
    assert.equal(blocks[0].children[0].type, "text");
});

test("подчёркивание внутри слова не выделяет текст", () => {
    const blocks = parse("Переменная snake_case\n");

    assert.equal(blocks[0].children.length, 1);
    assert.equal(blocks[0].children[0].type, "text");
});

test("таблица разбирается с выравниванием колонок", () => {
    const blocks = parse("| Тип | Описание |\n| :--- | ---: |\n| `int` | Целое |\n");

    const table = findBlock(blocks, "table");

    assert.equal(table.header.length, 2);
    assert.equal(table.header[0].align, "left");
    assert.equal(table.header[1].align, "right");
    assert.equal(table.rows.length, 1);
    assert.equal(table.rows[0][0].children[0].type, "code");
});

test("списки разбираются как маркированные и нумерованные", () => {
    const blocks = parse("- один\n- два\n\n1. первый\n2. второй\n");

    const lists = blocks.filter((block) => block.type === "list");

    assert.equal(lists.length, 2);
    assert.equal(lists[0].ordered, false);
    assert.equal(lists[0].items.length, 2);
    assert.equal(lists[1].ordered, true);
    assert.equal(lists[1].items.length, 2);
});

test("вложенный пункт попадает внутрь родительского", () => {
    const blocks = parse("- пункт\n  - вложенный\n");

    const list = findBlock(blocks, "list");
    const nested = list.items[0].blocks.find((block) => block.type === "list");

    assert.ok(nested);
    assert.equal(nested.items[0].children[0].value, "вложенный");
});

test("цитата разбирается в отдельный блок", () => {
    const blocks = parse("> Цитата\n> продолжение\n");

    const quote = findBlock(blocks, "quote");

    assert.ok(quote);
    assert.equal(quote.children[0].type, "paragraph");
});

test("блок кода сохраняется вместе с языком и подсветкой", () => {
    const blocks = parse("```python\nname = \"Иван\"\n```\n");

    const code = findBlock(blocks, "code");

    assert.equal(code.language, "python");
    assert.equal(code.code, "name = \"Иван\"");
    assert.ok(code.tokens.some((token) => token.type === "string"));
});

test("ссылка с опасным протоколом остаётся текстом", () => {
    const blocks = parse("[плохая](javascript:alert(1))\n");

    const types = blocks[0].children.map((node) => node.type);

    assert.ok(!types.includes("link"));
});

test("обычная ссылка превращается в узел", () => {
    const blocks = parse("[документация](https://example.com/docs)\n");

    const link = blocks[0].children.find((node) => node.type === "link");

    assert.equal(link.href, "https://example.com/docs");
});

test("изображение сохраняет подпись и адрес", () => {
    const blocks = parse("![Схема](assets/schema.png)\n");

    const image = blocks[0].children.find((node) => node.type === "image");

    assert.equal(image.alt, "Схема");
    assert.equal(image.src, "assets/schema.png");
});

test("кастомный блок разбирается и отдаётся как есть", () => {
    const blocks = parse(":::test\nКакой тип?\n:::\n");

    const custom = findBlock(blocks, "custom");

    assert.equal(custom.blockType, "test");
    assert.equal(custom.content, "Какой тип?");
    assert.equal(custom.implemented, false);
    assert.equal(custom.children[0].type, "paragraph");
});

test("незакрытый кастомный блок остаётся текстом", () => {
    const blocks = parse(":::test\nбез закрытия\n");

    assert.equal(findBlock(blocks, "custom"), undefined);
});

test("сервис принимает свой обработчик кастомного блока", () => {
    class VideoHandler extends CustomBlockHandler {
        constructor() {
            super("video");
        }

        parse(content) {
            return {type: this.type, content, implemented: true, data: {url: content}};
        }
    }

    const service = new MarkdownService();

    service.registerCustomBlock(new VideoHandler());

    const blocks = service.parse(":::video\nhttps://example.com/video.mp4\n:::\n");

    const custom = findBlock(blocks, "custom");

    assert.equal(custom.implemented, true);
    assert.equal(custom.data.url, "https://example.com/video.mp4");
});

test("html из урока остаётся текстом", () => {
    const blocks = parse("<script>alert(1)</script>\n");

    assert.equal(blocks[0].type, "paragraph");
    assert.equal(blocks[0].children[0].type, "text");
    assert.equal(blocks[0].children[0].value, "<script>alert(1)</script>");
});

test("проверка безопасности ссылок", () => {
    assert.equal(isSafeUrl("https://example.com"), true);
    assert.equal(isSafeUrl("mailto:mail@example.com"), true);
    assert.equal(isSafeUrl("/lessons/1"), true);
    assert.equal(isSafeUrl("javascript:alert(1)"), false);
    assert.equal(isSafeUrl("data:text/html;base64,PHNjcmlwdD4="), false);
    assert.equal(isSafeUrl("//evil.example.com"), false);
    assert.equal(isSafeUrl(""), false);
});
