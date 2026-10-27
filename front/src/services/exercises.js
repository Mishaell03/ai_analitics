/**
 * ЗАДАНИЯ УРОКА И ПРАВИЛЬНЫЕ ОТВЕТЫ
 *
 * Задание записывается в Markdown урока отдельным блоком:
 *
 *     :::test
 *     id: python-variables
 *     Текст задания
 *     - [ ] Вариант 1
 *     - [ ] Вариант 2
 *     :::
 *
 * Строка `id:` связывает задание с правильным ответом в базе:
 * ответ переживает правку текста задания. Идентификатор генерирует
 * фронтенд — короткий хеш из 10 символов; администратор может его
 * переименовать, но придумывать значение вручную не обязан.
 *
 * Правильные ответы хранятся отдельно от Markdown, поэтому в файл
 * уходят только варианты без отметок:
 *
 *     - [ ] Вариант 1
 *
 * Ответ задания — строка в JSON:
 *
 *     {"type": "choice", "correct": ["Вариант 1"]}   — выбор вариантов
 *     {"type": "text", "value": "print(value)"}      — старый ответ заданий
 *     {"type": "code", "value": "def solve(): ..."}  — эталонный ответ урока
 *
 * Эталонный ответ — это пример идеального решения задачи урока, а не
 * ответ конкретного задания. Он хранится в базе под отдельным ключом
 * и не привязан к идентификатору задания из Markdown: код ученика
 * с ним автоматически не сравнивается.
 */

export const ANSWER_TYPE_CHOICE = "choice";
export const ANSWER_TYPE_TEXT = "text";
export const ANSWER_TYPE_CODE = "code";

/**
 * Ключ эталонного ответа в базе.
 *
 * Ответы заданий адресуются идентификатором из Markdown (`id:`), а
 * эталонный ответ принадлежит уроку целиком, поэтому у него
 * собственный ключ, не зависящий ни от одного задания.
 */
export const REFERENCE_ANSWER_ID = "reference";

// идентификатор задания: те же буквы, цифры, дефис и подчёркивание,
// что и в шаблоне backend
const EXERCISE_ID_PATTERN = /^[A-Za-z0-9_-]{1,64}$/;

// строка с идентификатором задания
const EXERCISE_ID_LINE = /^id:\s*(?<exercise_id>[A-Za-z0-9_-]{1,64})\s*$/i;

/**
 * Автоматический идентификатор задания.
 *
 * Идентификатор придумывает фронтенд: администратору не нужно
 * вручную придумывать имя. Значение выглядит как короткий хеш из
 * 10 шестнадцатеричных символов, поэтому подходит под ограничения
 * backend и не содержит ничего лишнего.
 */
export const EXERCISE_ID_LENGTH = 10;

const EXERCISE_ID_ALPHABET = "0123456789abcdef";

/**
 * Случайные байты для идентификатора.
 *
 * crypto есть и в браузере, и в тестах Node; Math.random остаётся
 * запасным вариантом для старых окружений.
 *
 * @param {number} size количество байт
 * @returns {Uint8Array}
 */
function randomBytes(size) {
    const bytes = new Uint8Array(size);

    if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
        crypto.getRandomValues(bytes);

        return bytes;
    }

    for (let index = 0; index < size; index += 1) {
        bytes[index] = Math.floor(Math.random() * 256);
    }

    return bytes;
}

/**
 * Генерирует идентификатор задания из 10 символов.
 *
 * @returns {string}
 */
export function generateExerciseId() {
    return Array.from(
        randomBytes(EXERCISE_ID_LENGTH),
        (byte) => EXERCISE_ID_ALPHABET[byte % EXERCISE_ID_ALPHABET.length]
    ).join("");
}

// вариант ответа: маркер списка и квадратные скобки
const OPTION_LINE = /^(?<indent>\s*)[-*+]\s+\[(?<mark>[ xX])\]\s*(?<text>.*)$/;

// открывающая и закрывающая строки блока задания
const BLOCK_OPEN = /^:::\s*test\s*$/;
const BLOCK_CLOSE = /^:::\s*$/;

/**
 * Разбирает задания из Markdown урока.
 *
 * @param {string} markdown текст урока
 * @returns {object[]} задания: идентификатор, вопрос, варианты
 */
export function parseExercises(markdown) {
    return findBlocks(markdown).map((block) => {
        const idMatch = EXERCISE_ID_LINE.exec(block.body[0] ?? "");
        const exerciseId = idMatch ? idMatch.groups.exercise_id : "";
        const rest = idMatch ? block.body.slice(1) : block.body;

        const options = [];
        const questionLines = [];

        for (const line of rest) {
            const option = OPTION_LINE.exec(line);

            if (option) {
                options.push({
                    text: option.groups.text.trim(),
                    checked: option.groups.mark.toLowerCase() === "x",
                });

                continue;
            }

            questionLines.push(line);
        }

        return {
            exercise_id: exerciseId,
            question: questionLines.join("\n").trim(),
            options,
            body: rest.join("\n"),
            start: block.start,
            end: block.end,
        };
    });
}

/**
 * Блоки заданий в Markdown: границы нужны, чтобы править их по месту.
 *
 * @param {string} markdown текст урока
 * @returns {object[]}
 */
function findBlocks(markdown) {
    const lines = (markdown ?? "").split("\n");
    const blocks = [];

    let index = 0;

    while (index < lines.length) {
        if (!BLOCK_OPEN.test(lines[index])) {
            index += 1;
            continue;
        }

        const body = [];
        let cursor = index + 1;
        let closed = false;

        while (cursor < lines.length) {
            if (BLOCK_CLOSE.test(lines[cursor])) {
                closed = true;
                cursor += 1;
                break;
            }

            body.push(lines[cursor]);
            cursor += 1;
        }

        // незакрытый блок — обычный текст
        if (!closed) {
            index += 1;
            continue;
        }

        blocks.push({body, start: index, end: cursor});

        index = cursor;
    }

    return blocks;
}

/**
 * Убирает отметки правильных вариантов из Markdown.
 *
 * В файл урока варианты попадают без отметок: правильные ответы
 * лежат в базе и не должны утекать в содержимое урока.
 *
 * @param {string} markdown текст урока
 * @returns {string}
 */
export function stripCheckedMarks(markdown) {
    return (markdown ?? "").replace(
        /^(\s*[-*+]\s+\[)[ xX](\])/gm,
        "$1 $2"
    );
}

/**
 * Возвращает отметки правильных вариантов в Markdown.
 *
 * @param {string} markdown текст урока
 * @param {object} answers ответы по идентификатору задания
 * @returns {string}
 */
export function applyAnswers(markdown, answers) {
    if (!answers || !Object.keys(answers).length) {
        return markdown ?? "";
    }

    const blocks = findBlocks(markdown);
    const exercises = parseExercises(markdown);
    const lines = (markdown ?? "").split("\n");

    // блоки переписываем с конца: индексы строк не сбиваются
    for (let index = blocks.length - 1; index >= 0; index -= 1) {
        const block = blocks[index];
        const exercise = exercises[index];

        if (!exercise?.exercise_id) {
            continue;
        }

        const answer = answers[exercise.exercise_id];

        if (!answer || answer.type !== ANSWER_TYPE_CHOICE) {
            continue;
        }

        const correct = answer.correct ?? [];

        let bodyOffset = block.start + 1;

        // строка с идентификатором занимает первую строку тела блока
        if (EXERCISE_ID_LINE.test(lines[bodyOffset] ?? "")) {
            bodyOffset += 1;
        }

        for (let line = bodyOffset; line < block.end - 1; line += 1) {
            const option = OPTION_LINE.exec(lines[line]);

            if (!option) {
                continue;
            }

            const mark = correct.includes(option.groups.text.trim()) ? "x" : " ";

            lines[line] = `${option.groups.indent}- [${mark}] ${option.groups.text}`;
        }
    }

    return lines.join("\n");
}

/**
 * Отмечает или снимает отметку правильного варианта.
 *
 * @param {string} markdown текст урока
 * @param {number} exerciseIndex номер задания в уроке
 * @param {number} optionIndex номер варианта в задании
 * @param {boolean} checked новое состояние отметки
 * @returns {string}
 */
export function setOptionChecked(markdown, exerciseIndex, optionIndex, checked) {
    const exercises = parseExercises(markdown);
    const exercise = exercises[exerciseIndex];

    if (!exercise) {
        return markdown ?? "";
    }

    const lines = (markdown ?? "").split("\n");
    let optionSeen = 0;
    let bodyOffset = exercise.start + 1;

    // строка с идентификатором занимает первую строку тела блока
    if (EXERCISE_ID_LINE.test(lines[bodyOffset] ?? "")) {
        bodyOffset += 1;
    }

    for (let index = bodyOffset; index < exercise.end - 1; index += 1) {
        if (!OPTION_LINE.test(lines[index])) {
            continue;
        }

        if (optionSeen === optionIndex) {
            const option = OPTION_LINE.exec(lines[index]);
            const mark = checked ? "x" : " ";

            lines[index] = `${option.groups.indent}- [${mark}] ${option.groups.text}`;
            break;
        }

        optionSeen += 1;
    }

    return lines.join("\n");
}

/**
 * Записывает идентификатор задания в Markdown.
 *
 * @param {string} markdown текст урока
 * @param {number} exerciseIndex номер задания в уроке
 * @param {string} exerciseId новый идентификатор
 * @returns {string}
 */
export function setExerciseId(markdown, exerciseIndex, exerciseId) {
    const exercises = parseExercises(markdown);
    const exercise = exercises[exerciseIndex];

    if (!exercise) {
        return markdown ?? "";
    }

    const value = (exerciseId ?? "").trim();

    if (!EXERCISE_ID_PATTERN.test(value)) {
        return markdown ?? "";
    }

    const lines = (markdown ?? "").split("\n");
    const bodyStart = exercise.start + 1;
    const hasId = EXERCISE_ID_LINE.test(lines[bodyStart] ?? "");

    if (hasId) {
        lines[bodyStart] = `id: ${value}`;
    } else {
        lines.splice(bodyStart, 0, `id: ${value}`);
    }

    return lines.join("\n");
}

/**
 * Проставляет идентификаторы всем заданиям без них.
 *
 * Блоки с уже сохранённым `id:` не трогаются: по идентификатору к
 * заданию привязан правильный ответ в базе. Новым заданиям выдаётся
 * сгенерированный хеш, поэтому администратору не нужно придумывать
 * имя вручную.
 *
 * @param {string} markdown текст урока
 * @returns {string}
 */
export function ensureExerciseIds(markdown) {
    const source = markdown ?? "";
    const exercises = parseExercises(source);
    const used = new Set(
        exercises
            .map((exercise) => exercise.exercise_id)
            .filter(Boolean)
    );

    let result = source;

    // идём с конца: вставка строки не сдвигает индексы предыдущих блоков
    for (let index = exercises.length - 1; index >= 0; index -= 1) {
        if (exercises[index].exercise_id) {
            continue;
        }

        let exerciseId = generateExerciseId();

        while (used.has(exerciseId)) {
            exerciseId = generateExerciseId();
        }

        used.add(exerciseId);
        result = setExerciseId(result, index, exerciseId);
    }

    return result;
}

/**
 * Собирает ответ задания.
 *
 * Варианты отмечаются галочками в Markdown, поэтому их ответ
 * собирается из отметок. Ветка с вводом текста осталась для
 * ответов, сохранённых прежней версией: новые текстовые ответы
 * заданий не создаются, код хранится как эталонный ответ урока.
 *
 * @param {object} exercise задание из parseExercises
 * @param {string} textAnswer ответ для задания с вводом текста
 * @returns {string|null} ответ или null, если ответа нет
 */
export function buildAnswer(exercise, textAnswer) {
    if (!exercise) {
        return null;
    }

    if (exercise.options.length) {
        const correct = exercise.options
            .filter((option) => option.checked)
            .map((option) => option.text);

        if (!correct.length) {
            return null;
        }

        return JSON.stringify({type: ANSWER_TYPE_CHOICE, correct});
    }

    const value = (textAnswer ?? "").trim();

    if (!value) {
        return null;
    }

    return JSON.stringify({type: ANSWER_TYPE_TEXT, value});
}

/**
 * Собирает эталонный ответ урока.
 *
 * Код сохраняется как есть: идентификатор задания в него не
 * добавляется, иначе пример решения перестал бы быть кодом.
 *
 * @param {string} code пример идеального решения
 * @returns {string|null} ответ или null, если кода нет
 */
export function buildReferenceAnswer(code) {
    const value = (code ?? "").trim();

    if (!value) {
        return null;
    }

    return JSON.stringify({type: ANSWER_TYPE_CODE, value});
}

/**
 * Разбирает ответ из базы.
 *
 * Старые или чужие значения без JSON считаем текстовым ответом.
 *
 * @param {string} raw ответ из базы
 * @returns {{type: string, correct?: string[], value?: string}|null}
 */
export function parseAnswer(raw) {
    if (!raw) {
        return null;
    }

    try {
        const parsed = JSON.parse(raw);

        if (parsed && typeof parsed === "object"
            && (parsed.type === ANSWER_TYPE_CHOICE
                || parsed.type === ANSWER_TYPE_TEXT
                || parsed.type === ANSWER_TYPE_CODE)) {
            return parsed;
        }
    } catch {
        // ответ не в JSON — считаем его текстовым
    }

    return {type: ANSWER_TYPE_TEXT, value: raw};
}

/**
 * Ответы урока по идентификатору задания.
 *
 * Принимает и ответы из API (список), и готовую карту
 * идентификатор → ответ. Эталонный ответ урока сюда не попадает:
 * он не относится ни к одному заданию.
 *
 * @param {object[]|object} answers ответы из API или карта ответов
 * @returns {object}
 */
export function buildAnswerMap(answers) {
    const items = Array.isArray(answers)
        ? answers
        : Object.entries(answers ?? {}).map(([exercise_id, answer]) => ({exercise_id, answer}));

    const map = {};

    for (const item of items) {
        if (!item.exercise_id || item.exercise_id === REFERENCE_ANSWER_ID) {
            continue;
        }

        const parsed = parseAnswer(item.answer);

        if (parsed) {
            map[item.exercise_id] = parsed;
        }
    }

    return map;
}

/**
 * Эталонный ответ урока из ответов API.
 *
 * Возвращает и разобранное значение для формы, и сырую строку из
 * базы: по ней видно, изменился ли ответ перед сохранением.
 *
 * @param {object[]|object} answers ответы из API или карта ответов
 * @returns {{value: string, raw: string}}
 */
export function getReferenceAnswer(answers) {
    const items = Array.isArray(answers)
        ? answers.map((item) => [item.exercise_id, item.answer])
        : Object.entries(answers ?? {});

    const entry = items.find(([exerciseId]) => exerciseId === REFERENCE_ANSWER_ID);
    const raw = entry?.[1] ?? "";

    return {value: parseAnswer(raw)?.value ?? "", raw};
}
