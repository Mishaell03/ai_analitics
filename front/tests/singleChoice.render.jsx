import assert from "node:assert/strict";
import {renderToStaticMarkup} from "react-dom/server";
import {MemoryRouter} from "react-router-dom";
import {AuthProvider} from "@/context/AuthContext.jsx";
import Markdown from "@/components/Markdown/Markdown.jsx";
import LessonExercisesPanel from "@/pages/Admin/Lessons/LessonExercisesPanel.jsx";
import {parseExercises} from "@/services/exercises.js";

const source = ":::test\nid: single\nВыберите один\n- (х) Один\n- ( ) Два\n:::";
const markup = renderToStaticMarkup(<Markdown content={source}/>);
assert.equal((markup.match(/type="radio"/g) ?? []).length, 2);
assert.ok(!markup.includes('checked=""')); // отметка в md не открывает ответ ученику
const names = [...markup.matchAll(/name="([^"]+)"/g)].map((match) => match[1]);
assert.equal(names.length, 2);
assert.equal(new Set(names).size, 1);

const completed = renderToStaticMarkup(<Markdown content={source} answers={{
    single: {type: "single_choice", correct: ["Один"]},
}}/>);
assert.equal((completed.match(/checked=""/g) ?? []).length, 1);
assert.equal((completed.match(/disabled=""/g) ?? []).length, 2);
assert.match(completed, /data-completed="true"/);

const admin = renderToStaticMarkup(
    <MemoryRouter><AuthProvider><LessonExercisesPanel
        exercises={parseExercises(source)} onToggleOption={() => {}} onChangeId={() => {}}
    /></AuthProvider></MemoryRouter>
);
assert.equal((admin.match(/type="radio"/g) ?? []).length, 2);
assert.equal((admin.match(/checked=""/g) ?? []).length, 1);

const multiple = renderToStaticMarkup(<Markdown content={source.replaceAll("(х)", "[x]").replaceAll("( )", "[ ]")}/>);
assert.equal((multiple.match(/type="checkbox"/g) ?? []).length, 2);
assert.ok(!multiple.includes('checked=""'));

console.log("Выбор одного ответа: отрисовка ученика и админки прошла проверку");
