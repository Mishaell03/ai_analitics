import assert from "node:assert/strict";
import {renderToStaticMarkup} from "react-dom/server";
import {MemoryRouter} from "react-router-dom";
import Markdown from "@/components/Markdown/Markdown.jsx";
import Description from "@/components/Markdown/Description.jsx";
import {AuthProvider} from "@/context/AuthContext.jsx";
import {Dashboard} from "@/pages/Admin/Dashboard/Dashboard.jsx";
import {Users} from "@/pages/Admin/Users/Users.jsx";
import AdminCourses from "@/pages/Admin/Courses/AdminCourses.jsx";
import AdminLayout from "@/pages/Admin/AdminLayout.jsx";
import AdminSidebar from "@/pages/Admin/AdminSidebar.jsx";
import AdminPageHeader from "@/pages/Admin/components/AdminPageHeader.jsx";
import AdminPagination from "@/pages/Admin/components/AdminPagination.jsx";
import AdminModal from "@/pages/Admin/components/AdminModal.jsx";
import AdminToast from "@/pages/Admin/components/AdminToast.jsx";
import ConfirmModal from "@/components/ConfirmModal/ConfirmModal.jsx";
import CoursesTable from "@/pages/Admin/Courses/CoursesTable.jsx";
import ModulesTable from "@/pages/Admin/Courses/ModulesTable.jsx";
import CourseFormModal from "@/pages/Admin/Courses/CourseFormModal.jsx";
import ModuleFormModal from "@/pages/Admin/Courses/ModuleFormModal.jsx";
import CourseCoverModal from "@/pages/Admin/Courses/CourseCoverModal.jsx";
import LessonsPanel from "@/pages/Admin/Lessons/LessonsPanel.jsx";
import LessonsTable from "@/pages/Admin/Lessons/LessonsTable.jsx";
import LessonEditor from "@/pages/Admin/Lessons/LessonEditor.jsx";
import LessonContentModal from "@/pages/Admin/Lessons/LessonContentModal.jsx";
import LessonMediaModal from "@/pages/Admin/Lessons/LessonMediaModal.jsx";
import LessonExercisesPanel from "@/pages/Admin/Lessons/LessonExercisesPanel.jsx";
import UserModal from "@/pages/Admin/Users/UserModal.jsx";
import LessonMentor from "@/components/LessonMentor/LessonMentor.jsx";
import MentorTurn from "@/components/LessonMentor/MentorTurn.jsx";
import MentorWelcome from "@/components/LessonMentor/MentorWelcome.jsx";
import MentorText from "@/components/LessonMentor/MentorText.jsx";

/**
 * Проверка отрисовки Markdown и админки.
 *
 * Компоненты собираются в SSR-режиме Vite, поэтому здесь проверяется
 * именно разметка: какие элементы появились и как они выглядят.
 *
 * Запуск: npm run test:render
 */

const mentorHtml = renderToStaticMarkup(<LessonMentor slug="sql" moduleId="1" lessonId="2"/>);
assert.ok(mentorHtml.includes("AI-наставник"));
assert.ok(mentorHtml.includes("DeepSeek API"));
assert.ok(mentorHtml.startsWith("<aside"));
assert.ok(mentorHtml.includes('maxLength="2000"'));
assert.ok(!mentorHtml.includes("<script"));
assert.ok(mentorHtml.includes('role="log"'));
assert.ok(mentorHtml.includes("Ctrl / ⌘ + Enter"));
assert.ok(mentorHtml.includes("<details"));
assert.ok(mentorHtml.includes('placeholder="Что осталось непонятным в уроке?"'));

let promptCalls = 0;
const mentorWelcome = renderToStaticMarkup(<MentorWelcome onPrompt={() => { promptCalls += 1; }}/>);
assert.ok(mentorWelcome.includes("Сложная тема? Разберёмся."));
assert.equal((mentorWelcome.match(/<button/g) ?? []).length, 3);
assert.equal(promptCalls, 0);

const mentorAnswer = renderToStaticMarkup(<MentorTurn item={{
    question: "<img src=x onerror=alert(1)>", status: "completed",
    answer: "**Группировка** и `COUNT(*)`\n\n```sql\nSELECT COUNT(*) FROM orders;\n```",
}}/>);
assert.ok(mentorAnswer.includes("<strong>Группировка</strong>"));
assert.ok(mentorAnswer.includes("<code>COUNT(*)</code>"));
assert.ok(mentorAnswer.includes("<pre><code>SELECT COUNT(*) FROM orders;</code></pre>"));
assert.ok(mentorAnswer.includes("Скопировать ответ"));
assert.ok(!mentorAnswer.includes("<img"));
assert.ok(mentorAnswer.includes("&lt;img"));

const mentorUnsafeText = renderToStaticMarkup(<MentorText text={
    '<script>alert(1)</script> [link](https://example.com) ![image](https://example.com/image.png)'
}/>);
assert.ok(!/<(?:script|a|img)\b/.test(mentorUnsafeText));
assert.ok(mentorUnsafeText.includes("&lt;script&gt;"));

const mentorPending = renderToStaticMarkup(<MentorTurn item={{question: "SQL?", status: "pending"}}/>);
assert.ok(mentorPending.includes('role="status"'));
assert.ok(mentorPending.includes("Разбираюсь в вашем вопросе…"));
assert.ok(!mentorPending.includes("Скопировать ответ"));

const descriptionHtml = renderToStaticMarkup(<Description content={
    "Освойте анализ данных с нуля!\n\nВас ждут понятные объяснения.\n\n**Подходит новичкам без опыта программирования.**"
}/>);
const codeExerciseHtml = renderToStaticMarkup(<Markdown
    content={":::code python\nid: secret-test\n:::"}
    answers={{"secret-test": {type: "code", value: "SECRET_TEACHER_SOLUTION"}}}
/>);
assert.ok(codeExerciseHtml.includes("textarea"));
assert.ok(codeExerciseHtml.includes("Запустить"));
assert.ok(!codeExerciseHtml.includes("SECRET_TEACHER_SOLUTION"));
assert.equal((descriptionHtml.match(/<br\/>/g) ?? []).length, 2);
assert.equal((descriptionHtml.match(/aria-hidden="true"/g) ?? []).length, 2);
assert.ok(descriptionHtml.includes("<strong><span>Подходит новичкам без опыта программирования.</span></strong>"));

const source = [
    "# Заголовок урока",
    "",
    "Текст с **жирным**, *курсивом* и `кодом`.",
    "",
    "[документация](https://example.com/docs)",
    "",
    "[опасная](javascript:alert(1))",
    "",
    "| Тип | Описание |",
    "| --- | --- |",
    "| `int` | Целое |",
    "",
    "- пункт один",
    "- пункт два",
    "",
    "> Цитата урока",
    "",
    "```python",
    "name = \"Иван\"",
    "```",
    "",
    "![Схема](assets/variables.png)",
    "",
    "![Схема работы](asset:m_0123456789abcdef)",
    "",
    "![Ролик](asset:m_9876543210fedcba)",
    "",
    ":::test",
    "id: python-variables",
    "Какой тип вернёт `type(1.0)`?",
    "- [ ] Вариант 1",
    "- [ ] Вариант 2",
    ":::",
    "",
    ":::test",
    "id: python-code",
    "Напишите функцию",
    ":::",
    "",
    ":::test",
    "Какой тип вернёт `type(1.0)`?",
    ":::",
    "",
    "<script>alert(1)</script>",
].join("\n");

// медиафайлы урока: по идентификатору backend отдаёт временную ссылку
const media = {
    m_0123456789abcdef: {
        media_key: "m_0123456789abcdef",
        kind: "image",
        url: "http://localhost:9000/course-content/1/media/m_0123456789abcdef.webp",
    },
    m_9876543210fedcba: {
        media_key: "m_9876543210fedcba",
        kind: "video",
        url: "http://localhost:9000/course-content/1/media/m_9876543210fedcba.mp4",
    },
};

// правильные ответы на задания: приходят из базы, в разметке их нет
const answers = {
    "python-variables": {type: "choice", correct: ["Вариант 2"]},
    "python-code": {type: "text", value: "print(value)"},
};

const markup = renderToStaticMarkup(
    <Markdown
        content={source}
        media={media}
        answers={answers}
        labels={{answer: "Правильный ответ"}}
    />
);

// заголовки, абзацы и выделение
assert.match(markup, /<h1[^>]*>[\s\S]*?Заголовок урока[\s\S]*?<\/h1>/);
assert.match(markup, /<strong>[\s\S]*?жирным[\s\S]*?<\/strong>/);
assert.match(markup, /<em>[\s\S]*?курсивом[\s\S]*?<\/em>/);
assert.match(markup, /<code[^>]*>кодом<\/code>/);

// таблица
assert.match(markup, /<table[^>]*>/);
assert.match(markup, /<th[^>]*>[\s\S]*?Тип[\s\S]*?<\/th>/);

// списки и цитата
assert.match(markup, /<ul[^>]*>[\s\S]*?пункт один[\s\S]*?<\/ul>/);
assert.match(markup, /<blockquote[^>]*>/);

// блок кода с подсветкой
assert.match(markup, /<pre[^>]*>/);
assert.match(markup, /python/);
assert.match(markup, /tokenString/);

// картинка без готовой ссылки показывается заглушкой
assert.match(markup, /imagePlaceholder[^>]*>Схема</);

// ссылка на медиа раскрывается по идентификатору
assert.match(markup, /<img[^>]*m_0123456789abcdef\.webp/);
assert.match(markup, /<video[^>]*m_9876543210fedcba\.mp4/);
assert.ok(!markup.includes("asset:m_"));

// задание показывается отдельным блоком
assert.match(markup, /testBlock/);

// задание: варианты с чекбоксами, правильный отмечен
assert.match(markup, /python-variables/);
assert.match(markup, /Вариант 1/);
assert.match(markup, /Вариант 2/);
assert.match(markup, /type="checkbox"[^>]*checked=""/);
assert.match(markup, /data-correct="true"/);

// ответ с вводом кода показан отдельным полем
assert.match(markup, /Правильный ответ/);
assert.match(markup, /print\(value\)/);

// опасная ссылка остаётся текстом, а не ссылкой
assert.ok(!markup.includes('href="javascript:'));
assert.match(markup, /\[опасная\]/);

// html не превращается в элементы
assert.ok(!markup.includes("<script>"));
assert.match(markup, /&lt;script&gt;/);

console.log("Markdown отрисовывается корректно");

/* ---------- админка ---------- */

// страницы админки живут внутри провайдера сессии и роутера
const renderAdmin = (node) => renderToStaticMarkup(
    <MemoryRouter>
        <AuthProvider>{node}</AuthProvider>
    </MemoryRouter>
);

const adminCases = {
    Dashboard: <Dashboard/>,
    Users: <Users/>,
    AdminCourses: <AdminCourses/>,
    AdminLayout: <AdminLayout/>,
    AdminSidebar: <AdminSidebar/>,
    AdminPageHeader: (
        <AdminPageHeader eyebrow="Раздел" title="Заголовок" subtitle="Описание"/>
    ),
    AdminPagination: (
        <AdminPagination
            page={1}
            totalPages={3}
            onPrevious={() => {}}
            onNext={() => {}}
            label="Страница 1 из 3"
            previousLabel="Назад"
            nextLabel="Вперёд"
        />
    ),
    AdminToast: <AdminToast message={{type: "success", text: "Готово"}}/>,
    AdminModal: (
        <AdminModal onClose={() => {}} ariaLabel="Окно">
            <p>Содержимое окна</p>
        </AdminModal>
    ),
    ConfirmModal: (
        <ConfirmModal
            title="Удалить?"
            description="Курс"
            confirmText="Удалить"
            busyText="Удаление..."
            cancelText="Отмена"
            onConfirm={() => {}}
            onClose={() => {}}
        />
    ),
    CoursesTable: (
        <CoursesTable
            courses={[{slug: "s", title: "Курс", is_active: true}]}
            page={1}
            totalPages={1}
            loading={false}
            saving={false}
            onSelectCourse={() => {}}
            onCreateCourse={() => {}}
            onOpenCover={() => {}}
            onEditCourse={() => {}}
            onToggleStatus={() => {}}
            onDeleteCourse={() => {}}
            onPreviousPage={() => {}}
            onNextPage={() => {}}
        />
    ),
    ModulesTable: (
        <ModulesTable
            courses={[{slug: "s", title: "Курс"}]}
            selectedCourseSlug=""
            selectedModuleId={null}
            modules={[]}
            loading={false}
            error={null}
            reordering={false}
            saving={false}
            dragIndex={null}
            dragOverIndex={null}
            getDragProps={() => ({})}
            onSelectCourse={() => {}}
            onCreateModule={() => {}}
            onRetry={() => {}}
            onSelectModule={() => {}}
            onEditModule={() => {}}
            onToggleStatus={() => {}}
            onDeleteModule={() => {}}
        />
    ),
    CourseFormModal: (
        <CourseFormModal
            mode="create"
            course={{title: "", slug: "", description: "", is_active: false}}
            saving={false}
            onClose={() => {}}
            onSubmit={() => {}}
            onError={() => {}}
        />
    ),
    ModuleFormModal: (
        <ModuleFormModal
            mode="create"
            module={{title: "", description: "", is_active: false}}
            saving={false}
            onClose={() => {}}
            onSubmit={() => {}}
            onError={() => {}}
        />
    ),
    CourseCoverModal: (
        <CourseCoverModal
            course={{slug: "s", title: "Курс"}}
            onClose={() => {}}
            onSaved={() => {}}
        />
    ),
    LessonsPanel: <LessonsPanel courseSlug="" module={null}/>,
    LessonsTable: (
        <LessonsTable
            lessons={[]}
            loading={false}
            error={null}
            reordering={false}
            saving={false}
            dragIndex={null}
            dragOverIndex={null}
            getDragProps={() => ({})}
            onRetry={() => {}}
            onEdit={() => {}}
            onToggleStatus={() => {}}
            onOpen={() => {}}
            onDelete={() => {}}
        />
    ),
    LessonEditor: (
        <LessonEditor
            courseSlug="s"
            moduleId={1}
            lesson={null}
            onClose={() => {}}
            onSaved={() => {}}
        />
    ),
    LessonContentModal: (
        <LessonContentModal
            courseSlug="s"
            moduleId={1}
            lesson={{lesson_id: 1, title: "Урок", position: 1, is_published: false}}
            onClose={() => {}}
            onEdit={() => {}}
        />
    ),
    LessonMediaModal: (
        <LessonMediaModal
            courseSlug="s"
            moduleId={1}
            lesson={{lesson_id: 1, title: "Урок"}}
            onClose={() => {}}
            onChanged={() => {}}
        />
    ),
    LessonExercisesPanel: (
        <LessonExercisesPanel
            exercises={[{
                exercise_id: "python-variables",
                question: "Какой тип?",
                options: [{text: "Вариант 1", checked: true}],
            }]}
            onToggleOption={() => {}}
            onChangeId={() => {}}
        />
    ),
    UserModal: (
        <UserModal userId={1} onClose={() => {}} onUserUpdated={() => {}}/>
    ),
};

for (const [name, node] of Object.entries(adminCases)) {
    const adminMarkup = renderAdmin(node);

    assert.ok(adminMarkup.length > 0, `${name} не отрисовался`);
}

// страница курсов показывает заголовок раздела из переводов
const coursesMarkup = renderAdmin(<AdminCourses/>);

assert.match(coursesMarkup, /Управление курсами/);
assert.match(coursesMarkup, /Курсы и модули/);

console.log("Админка отрисовывается корректно");
