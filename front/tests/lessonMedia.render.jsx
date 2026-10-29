import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {renderToStaticMarkup} from "react-dom/server";
import Markdown from "@/components/Markdown/Markdown.jsx";
import {loadLessonMediaMap} from "@/services/media.js";
import {API_ROUTES} from "@/api/routes.js";

// Та же разметка, что в seed урока: идентификатор без расширения файла.
const source = "![m_bb0da2e8512e410c](asset:m_bb0da2e8512e410c)";
const media = await loadLessonMediaMap(async () => ({
    total_pages: 1,
    media: [{media_key: "m_bb0da2e8512e410c", kind: "video", url: "https://example.com/lesson.mp4?signature=test"}],
}));
const html = renderToStaticMarkup(<Markdown content={source} media={media}/>);
assert.match(html, /<video[^>]*src="https:\/\/example.com\/lesson.mp4\?signature=test"[^>]*controls=""/);
assert.ok(!html.includes("imagePlaceholder"));
assert.ok(!html.includes("asset:"));

assert.equal(API_ROUTES.COURSE_LESSON_MEDIA("demo", 1, 2), "/courses/demo/modules/1/lessons/2/media");
assert.equal(API_ROUTES.COURSE_LESSON_MEDIA_URL("demo", 1, 2, "m_bb0da2e8512e410c"),
    "/courses/demo/modules/1/lessons/2/media/m_bb0da2e8512e410c/url");

// Регрессия: пользовательская страница должна передавать карту файлов в Markdown.
const lesson = readFileSync("src/pages/Curses/Lesson.jsx", "utf8");
assert.match(lesson, /<Markdown[^>]*media=\{media\}[^>]*onMediaError=\{handleMediaError\}/);
console.log("Видео урока отрисовывается плеером по пользовательской временной ссылке");
