import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {renderToStaticMarkup} from "react-dom/server";
import Markdown from "@/components/Markdown/Markdown.jsx";
import {ExpertSolutionView} from "@/components/Markdown/MarkdownExpertSolution.jsx";
import {API_ROUTES} from "@/api/routes.js";

const content = ":::code python\nid: code-1\n:::";
const before = renderToStaticMarkup(<Markdown content={content} onExpertSolution={async () => {}}/>);
assert.ok(!before.includes("Решение от эксперта"));

const completed = renderToStaticMarkup(<Markdown content={content}
    answers={{"code-1": {type: "code", value: "print(42)"}}} onExpertSolution={async () => {}}/>);
assert.ok(completed.includes("Решение от эксперта"));
assert.ok(completed.includes("Загружаем решение эксперта"));
assert.ok(completed.indexOf("Решение от эксперта") > completed.indexOf("</textarea>"));

const reviewed = renderToStaticMarkup(<Markdown content={":::code sql\nid: sql-1\n:::"}
    expertReviewExercises={["sql-1"]} onExpertSolution={async () => {}}/>);
assert.ok(reviewed.includes("Решение от эксперта"));
assert.ok(!reviewed.includes("<textarea") || !reviewed.includes("SELECT"));
const other = renderToStaticMarkup(<Markdown content={":::code sql\nid: sql-2\n:::"}
    expertReviewExercises={["sql-1"]} onExpertSolution={async () => {}}/>);
assert.ok(!other.includes("Решение от эксперта"));
const practice = renderToStaticMarkup(<Markdown content={":::code sql\nid: none\n:::"}
    onExpertSolution={async () => {}}/>);
assert.ok(practice.includes("Поле для свободной практики"));
assert.ok(!practice.includes("Решение от эксперта"));

// Проверяем все три редактора самого урока, а не только сокращённый пример.
let slot = 0;
const lesson12 = readFileSync("../backend/infra/minio/seeds/course-content/1/4/12.md", "utf8")
    .replaceAll("id: none", () => `id: fixture_${++slot}`);
const lessonHtml = renderToStaticMarkup(<Markdown content={lesson12} onExpertSolution={async () => {}}/>);
const editors = [...lessonHtml.matchAll(/<textarea[^>]*>([\s\S]*?)<\/textarea>/g)];
assert.equal(editors.length, 3);
assert.ok(editors.every((match) => match[1] === ""));
assert.ok(!lessonHtml.includes("Решение от эксперта"));

for (const language of ["python", "sql"]) {
    const html = renderToStaticMarkup(<ExpertSolutionView solution={{
        exercise_id: "code-1", language, code: "<script>alert('EXPERT_SECRET')</script>",
    }}/>);
    assert.ok(html.includes("Решение от эксперта"));
    assert.ok(html.includes("EXPERT_SECRET"));
    assert.ok(!html.includes("<script>"));
    assert.match(html, /<pre[^>]*><code>/);
    assert.ok(html.includes(language));
}
assert.equal(API_ROUTES.COURSE_EXPERT_SOLUTION("demo", 2, 3, "code-1"),
    "/courses/demo/modules/2/lessons/3/exercises/code-1/expert-solution");
console.log("Решение эксперта: отдельный блок после редактора, подсветка и безопасный вывод");
