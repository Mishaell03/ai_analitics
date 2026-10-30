import assert from "node:assert/strict";
import {test} from "node:test";

import {
    ASSET_PREFIX,
    buildAssetMarkdown,
    formatDuration,
    getFileKind,
    getMediaAlt,
    loadLessonMediaMap,
    parseAssetReference,
    validateMediaFile,
} from "../src/services/media.js";
import {isSafeUrl} from "../src/services/markdown/sanitize.js";
import {markdownService} from "../src/services/markdown/MarkdownService.js";

function makeFile(name, type, size = 1024) {
    return {name, type, size};
}

test("медиа урока загружаются со всех страниц с типом и временной ссылкой", async () => {
    const calls = [];
    const video = {media_key: "m_bb0da2e8512e410c", kind: "video", url: "https://example.com/video.mp4"};
    const image = {media_key: "m_0123456789abcdef", kind: "image", url: "https://example.com/image.webp"};
    const map = await loadLessonMediaMap(async (page) => {
        calls.push(page);
        return {total_pages: 2, media: page === 1 ? [image] : [video]};
    });
    assert.deepEqual(calls, [1, 2]);
    assert.deepEqual(map, {[image.media_key]: image, [video.media_key]: video});
});

test("урок без медиа получает пустую карту", async () => {
    assert.deepEqual(await loadLessonMediaMap(async () => ({total_pages: 0, media: []})), {});
});

test("ошибка загрузки страницы медиа не скрывается неполным списком", async () => {
    await assert.rejects(loadLessonMediaMap(async (page) => {
        if (page === 2) throw new Error("Media unavailable");
        return {total_pages: 2, media: []};
    }), /Media unavailable/);
});

test("тип файла определяется по расширению и mime-типу", () => {
    assert.equal(getFileKind(makeFile("scheme.png", "image/png")), "image");
    assert.equal(getFileKind(makeFile("scheme.JPG", "")), "image");
    assert.equal(getFileKind(makeFile("lesson.mp4", "video/mp4")), "video");
    assert.equal(getFileKind(makeFile("notes.pdf", "application/pdf")), null);
    assert.equal(getFileKind(null), null);
});

test("файл неподходящего типа не проходит проверку", () => {
    const invalid = validateMediaFile(makeFile("notes.pdf", "application/pdf"));

    assert.equal(invalid.code, "mediaFileTypeNotAllowed");
});

test("файл больше лимита не проходит проверку", () => {
    const invalid = validateMediaFile(makeFile("big.mp4", "video/mp4", 300 * 1024 * 1024));

    assert.equal(invalid.code, "mediaFileTooLarge");
    assert.ok(invalid.params.limit);
});

test("подходящий файл проходит проверку", () => {
    assert.equal(validateMediaFile(makeFile("scheme.png", "image/png")), null);
});

test("идентификатор медиа разбирается из ссылки asset:", () => {
    assert.equal(parseAssetReference("asset:m_0123456789abcdef"), "m_0123456789abcdef");
    assert.equal(parseAssetReference("https://example.com/image.png"), null);
    assert.equal(parseAssetReference("asset:../secret"), null);
    assert.equal(parseAssetReference(""), null);
});

test("схема asset разрешена в разметке", () => {
    assert.equal(isSafeUrl("asset:m_0123456789abcdef"), true);
    assert.equal(isSafeUrl("javascript:alert(1)"), false);
});

test("markdown-вставка строится по идентификатору файла", () => {
    const media = {media_key: "m_0123456789abcdef", original_name: "scheme.png"};

    assert.equal(
        buildAssetMarkdown(media, "Схема"),
        `![Схема](${ASSET_PREFIX}m_0123456789abcdef)`
    );
});

test("подпись файла берётся из имени без расширения", () => {
    assert.equal(getMediaAlt({media_key: "m_1", original_name: "scheme.png"}), "scheme");
    assert.equal(getMediaAlt({media_key: "m_1"}), "m_1");
});

test("длительность видео форматируется в минуты и секунды", () => {
    assert.equal(formatDuration(65), "1:05");
    assert.equal(formatDuration(9), "0:09");
    assert.equal(formatDuration(0), "");
});

test("ссылка на медиа не теряется при разборе markdown", () => {
    const blocks = markdownService.parse("![Схема](asset:m_0123456789abcdef)\n");

    const image = blocks[0].children.find((node) => node.type === "image");

    assert.equal(image.src, "asset:m_0123456789abcdef");
    assert.equal(image.alt, "Схема");
});
