import assert from "node:assert/strict";
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
