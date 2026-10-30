import assert from "node:assert/strict";
import {renderToStaticMarkup} from "react-dom/server";
import {MemoryRouter} from "react-router-dom";
import LessonNavigation from "@/pages/Curses/LessonNavigation.jsx";

const render = (navigation) => renderToStaticMarkup(
    <MemoryRouter><LessonNavigation navigation={navigation} slug="demo"/></MemoryRouter>
);
const html = render({
    previous: {module_id: 1, lesson_id: 2},
    next: {module_id: 2, lesson_id: 3},
});
assert.match(html, /href="[^"]*\/demo\/modules\/1\/lessons\/2"/);
assert.match(html, /href="[^"]*\/demo\/modules\/2\/lessons\/3"/);
assert.ok(!html.includes("<button"));
assert.ok(!html.includes("<form"));
assert.ok(html.includes("Просмотреть предыдущий урок"));
assert.ok(html.includes("Просмотреть следующий урок"));
assert.ok(!render({previous: null, next: null}).includes("href="));
assert.match(render({loading: true}), /role="status"/);
assert.match(render({error: true}), /role="alert"/);
console.log("Просмотр уроков: ссылки без отправки ответов и завершения урока");
