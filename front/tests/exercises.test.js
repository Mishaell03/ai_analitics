import assert from "node:assert/strict";
import {test} from "node:test";

import {
    ANSWER_TYPE_CHOICE,
    ANSWER_TYPE_SINGLE_CHOICE,
    ANSWER_TYPE_CODE,
    ANSWER_TYPE_TEXT,
    REFERENCE_ANSWER_ID,
    applyAnswers,
    buildAnswer,
    buildAnswerMap,
    buildReferenceAnswer,
    ensureExerciseIds,
    generateExerciseId,
    getReferenceAnswer,
    parseAnswer,
    parseExercises,
    setExerciseId,
    setOptionChecked,
    stripCheckedMarks,
} from "../src/services/exercises.js";
import {markdownService} from "../src/services/markdown/MarkdownService.js";

const LESSON = [
    "# Переменные",
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
].join("\n");

const SINGLE_LESSON = ":::test\nid: single\nВыберите один ответ\n- ( ) Один\n- ( ) Два\n:::\n";

test("круглые скобки разбираются как выбор одного ответа", () => {
    const [exercise] = parseExercises(SINGLE_LESSON);
    assert.equal(exercise.singleChoice, true);
    assert.equal(exercise.question, "Выберите один ответ");
    assert.equal(exercise.options.length, 2);
    assert.ok(exercise.options.every((option) => !option.checked));
    for (const mark of ["x", "X", "х", "Х"]) {
        assert.equal(parseExercises(SINGLE_LESSON.replace("( )", `(${mark})`))[0].options[0].checked, true);
    }
});

test("выбор нового единственного ответа снимает предыдущий только в этом задании", () => {
    const source = SINGLE_LESSON + LESSON;
    const first = setOptionChecked(source, 0, 0, true);
    const second = setOptionChecked(first, 0, 1, true);
    assert.deepEqual(parseExercises(second)[0].options.map((option) => option.checked), [false, true]);
    assert.ok(second.endsWith(LESSON));
    assert.equal(setOptionChecked(second, 0, 9, true), second);
});

test("единственный ответ хранится отдельно и восстанавливается только для админки", () => {
    const marked = setOptionChecked(SINGLE_LESSON, 0, 1, true);
    const answer = buildAnswer(parseExercises(marked)[0]);
    assert.deepEqual(JSON.parse(answer), {type: ANSWER_TYPE_SINGLE_CHOICE, correct: ["Два"]});
    const uploaded = stripCheckedMarks(marked);
    assert.equal(uploaded, SINGLE_LESSON);
    const map = buildAnswerMap([{exercise_id: "single", answer}]);
    assert.equal(applyAnswers(uploaded, map), marked);
    assert.match(marked, /- \(х\) Два/);
});

test("пустой, множественный и смешанный single choice не собираются", () => {
    assert.equal(buildAnswer(parseExercises(SINGLE_LESSON)[0]), null);
    const multiple = SINGLE_LESSON.replaceAll("( )", "(х)");
    assert.equal(buildAnswer(parseExercises(multiple)[0]), null);
    const mixed = SINGLE_LESSON.replace("( )", "[x]");
    assert.equal(buildAnswer(parseExercises(mixed)[0]), null);
});

test("очистка удаляет латинские и русские отметки обоих видов", () => {
    for (const mark of ["x", "X", "х", "Х"]) {
        assert.equal(stripCheckedMarks(`- (${mark}) Один\n- [${mark}] Два`), "- ( ) Один\n- [ ] Два");
    }
});

test("задания разбираются из markdown урока", () => {
    const exercises = parseExercises(LESSON);

    assert.equal(exercises.length, 2);

    assert.equal(exercises[0].exercise_id, "python-variables");
    assert.equal(exercises[0].question, "Какой тип вернёт `type(1.0)`?");
    assert.equal(exercises[0].options.length, 2);
    assert.equal(exercises[0].options[0].text, "Вариант 1");
    assert.equal(exercises[0].options[0].checked, false);

    // задание без вариантов: ответ вводится текстом
    assert.equal(exercises[1].exercise_id, "python-code");
    assert.equal(exercises[1].options.length, 0);
});

test("задание без идентификатора остаётся без ответа", () => {
    const exercises = parseExercises(":::test\nВопрос\n- [ ] Вариант\n:::\n");

    assert.equal(exercises.length, 1);
    assert.equal(exercises[0].exercise_id, "");
    assert.equal(exercises[0].options.length, 1);
});

test("незакрытый блок не считается заданием", () => {
    assert.equal(parseExercises(":::test\nВопрос\n").length, 0);
});

test("отметки правильных вариантов убираются из markdown", () => {
    const marked = ":::test\nid: a\n- [x] Один\n- [ ] Два\n:::\n";

    assert.equal(
        stripCheckedMarks(marked),
        ":::test\nid: a\n- [ ] Один\n- [ ] Два\n:::\n"
    );
});

test("в файл урока отметки ответов не попадают", () => {
    const marked = setOptionChecked(LESSON, 0, 1, true);

    assert.match(marked, /- \[ \] Вариант 1/);
    assert.match(marked, /- \[x\] Вариант 2/);

    const uploaded = stripCheckedMarks(marked);

    assert.ok(!uploaded.includes("[x]"));
    assert.match(uploaded, /- \[ \] Вариант 2/);
});

test("отметка ставится только нужному варианту", () => {
    const marked = setOptionChecked(LESSON, 0, 0, true);

    assert.match(marked, /- \[x\] Вариант 1/);
    assert.match(marked, /- \[ \] Вариант 2/);
});

test("идентификатор задания записывается в markdown", () => {
    const withId = setExerciseId(LESSON, 1, "new-code");

    assert.match(withId, /id: new-code/);
    assert.equal(parseExercises(withId)[1].exercise_id, "new-code");
});

test("идентификатор добавляется, если его не было", () => {
    const source = ":::test\nВопрос\n- [ ] Вариант\n:::\n";
    const withId = setExerciseId(source, 0, "generated-id");

    assert.match(withId, /id: generated-id/);
    assert.equal(parseExercises(withId)[0].exercise_id, "generated-id");
});

test("некорректный идентификатор не записывается", () => {
    assert.equal(setExerciseId(LESSON, 0, "плохой id"), LESSON);
});

test("автоматический идентификатор — хеш из 10 символов", () => {
    const exerciseId = generateExerciseId();

    assert.equal(exerciseId.length, 10);
    assert.match(exerciseId, /^[0-9a-f]{10}$/);
});

test("идентификаторы проставляются только заданиям без id", () => {
    const source = [
        ":::test",
        "id: keep-me",
        "Вопрос с id",
        "- [ ] Вариант",
        ":::",
        "",
        ":::test",
        "Вопрос без id",
        "- [ ] Вариант",
        ":::",
    ].join("\n");

    const withIds = ensureExerciseIds(source);
    const exercises = parseExercises(withIds);

    // сохранённый идентификатор не меняется: к нему привязан ответ
    assert.equal(exercises[0].exercise_id, "keep-me");
    assert.match(exercises[1].exercise_id, /^[0-9a-f]{10}$/);

    // повторный вызов ничего не добавляет
    assert.equal(ensureExerciseIds(withIds), withIds);
});

test("ответы на варианты собираются из отметок", () => {
    const marked = setOptionChecked(LESSON, 0, 0, true);
    const answer = buildAnswer(parseExercises(marked)[0], "");

    assert.deepEqual(JSON.parse(answer), {
        type: ANSWER_TYPE_CHOICE,
        correct: ["Вариант 1"],
    });
});

test("без отмеченных вариантов ответа нет", () => {
    assert.equal(buildAnswer(parseExercises(LESSON)[0], ""), null);
});

test("ответ с вводом текста сохраняется отдельным полем", () => {
    const answer = buildAnswer(parseExercises(LESSON)[1], "print(value)");

    assert.deepEqual(JSON.parse(answer), {
        type: ANSWER_TYPE_TEXT,
        value: "print(value)",
    });
});

test("ответ разбирается из базы", () => {
    const parsed = parseAnswer(JSON.stringify({type: ANSWER_TYPE_CHOICE, correct: ["A"]}));

    assert.equal(parsed.type, ANSWER_TYPE_CHOICE);
    assert.deepEqual(parsed.correct, ["A"]);

    // обычная строка считается текстовым ответом
    assert.equal(parseAnswer("print").type, ANSWER_TYPE_TEXT);
    assert.equal(parseAnswer("print").value, "print");
    assert.equal(parseAnswer(""), null);
});

test("ответы урока собираются по идентификатору задания", () => {
    const map = buildAnswerMap([
        {exercise_id: "python-variables", answer: JSON.stringify({type: ANSWER_TYPE_CHOICE, correct: ["Вариант 1"]})},
        {exercise_id: "python-code", answer: "print"},
    ]);

    assert.equal(Object.keys(map).length, 2);
    assert.deepEqual(map["python-variables"].correct, ["Вариант 1"]);
    assert.equal(map["python-code"].value, "print");
});

test("карта ответов тоже принимается", () => {
    const map = buildAnswerMap({
        "python-code": "print",
    });

    assert.equal(map["python-code"].value, "print");
});

test("отметки ответов возвращаются в markdown", () => {
    const answers = {
        "python-variables": {type: ANSWER_TYPE_CHOICE, correct: ["Вариант 2"]},
    };

    const restored = applyAnswers(LESSON, answers);

    assert.match(restored, /- \[ \] Вариант 1/);
    assert.match(restored, /- \[x\] Вариант 2/);
});

test("полный круг: отметка, ответ в базу и обратно", () => {
    const marked = setOptionChecked(LESSON, 0, 0, true);
    const answer = buildAnswer(parseExercises(marked)[0], "");

    // в файл урока уходит разметка без отметок
    const uploaded = stripCheckedMarks(marked);

    assert.ok(!uploaded.includes("[x]"));

    // ответ сохраняется отдельно и возвращает отметки при правке
    const answers = buildAnswerMap([{exercise_id: "python-variables", answer}]);
    const restored = applyAnswers(uploaded, answers);

    assert.match(restored, /- \[x\] Вариант 1/);
});

test("сервис markdown разбирает блок задания", () => {
    const blocks = markdownService.parse(LESSON);
    const custom = blocks.find((block) => block.type === "custom");

    assert.equal(custom.blockType, "test");
    assert.equal(custom.data.exercise_id, "python-variables");
    assert.match(custom.data.body, /Вариант 1/);
});

/* ---------- эталонный ответ урока ---------- */

const REFERENCE_CODE = [
    "def solve(values):",
    "    return [value * 2 for value in values]",
].join("\n");

test("эталонный ответ хранится под ключом урока, а не задания", () => {
    // ключ не совпадает ни с одним идентификатором задания из Markdown
    const ids = parseExercises(LESSON).map((exercise) => exercise.exercise_id);

    assert.ok(REFERENCE_ANSWER_ID);
    assert.ok(!ids.includes(REFERENCE_ANSWER_ID));
});

test("код сохраняется как есть: идентификатор в него не добавляется", () => {
    const answer = buildReferenceAnswer(REFERENCE_CODE);
    const parsed = JSON.parse(answer);

    assert.deepEqual(parsed, {type: ANSWER_TYPE_CODE, value: REFERENCE_CODE});

    // ни идентификатор задания, ни служебный ключ внутрь кода не попали
    assert.ok(!parsed.value.includes(REFERENCE_ANSWER_ID));
    assert.ok(!parsed.value.includes("python-code"));
});

test("пустой эталонный ответ не сохраняется", () => {
    assert.equal(buildReferenceAnswer(""), null);
    assert.equal(buildReferenceAnswer("   \n  "), null);
    assert.equal(buildReferenceAnswer(null), null);
});

test("эталонный ответ разбирается из базы", () => {
    const parsed = parseAnswer(buildReferenceAnswer(REFERENCE_CODE));

    assert.equal(parsed.type, ANSWER_TYPE_CODE);
    assert.equal(parsed.value, REFERENCE_CODE);
});

test("карта ответов заданий не содержит эталонный ответ", () => {
    const map = buildAnswerMap([
        {exercise_id: "python-variables", answer: JSON.stringify({type: ANSWER_TYPE_CHOICE, correct: ["А"]})},
        {exercise_id: REFERENCE_ANSWER_ID, answer: buildReferenceAnswer(REFERENCE_CODE)},
    ]);

    assert.deepEqual(Object.keys(map), ["python-variables"]);
});

test("эталонный ответ читается из ответов API", () => {
    const reference = getReferenceAnswer([
        {exercise_id: "python-variables", answer: "print"},
        {exercise_id: REFERENCE_ANSWER_ID, answer: buildReferenceAnswer(REFERENCE_CODE)},
    ]);

    assert.equal(reference.value, REFERENCE_CODE);
    assert.equal(reference.raw, buildReferenceAnswer(REFERENCE_CODE));
});

test("у урока без эталонного ответа значение пустое", () => {
    assert.deepEqual(getReferenceAnswer([]), {value: "", raw: ""});
    assert.deepEqual(getReferenceAnswer({}), {value: "", raw: ""});
});

test("эталонный ответ не подставляется в задания", () => {
    const answers = {
        [REFERENCE_ANSWER_ID]: {type: ANSWER_TYPE_CODE, value: REFERENCE_CODE},
    };

    assert.equal(applyAnswers(LESSON, answers), LESSON);
});
