import {api} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

/**
 * API-КЛИЕНТ ПРАВИЛЬНЫХ ОТВЕТОВ
 *
 * Задания лежат в Markdown урока, а правильные ответы — в базе.
 * Связь идёт через exercise_id: идентификатор задания из Markdown.
 *
 * Ответ — это строка, формат которой знает только клиент:
 * разбор и сборка живут в services/exercises.js.
 */

/**
 * Все правильные ответы урока.
 *
 * @param {number} lessonId id урока
 * @returns {Promise<{lesson_id: number, answers: object[]}>}
 */
export async function listExerciseAnswers(lessonId) {
    const {data} = await api.get(API_ROUTES.ADMIN_LESSON_EXERCISES(lessonId));

    return data;
}

/**
 * Создаёт или обновляет правильный ответ задания.
 *
 * @param {number} lessonId id урока
 * @param {string} exerciseId идентификатор задания
 * @param {string} answer ответ в формате сервиса
 * @returns {Promise<object>}
 */
export async function setExerciseAnswer(lessonId, exerciseId, answer) {
    const {data} = await api.post(
        API_ROUTES.ADMIN_LESSON_EXERCISE_ANSWER(lessonId, exerciseId),
        {answer}
    );

    return data;
}

/**
 * Удаляет правильный ответ задания.
 *
 * @param {number} lessonId id урока
 * @param {string} exerciseId идентификатор задания
 * @returns {Promise<object>}
 */
export async function deleteExerciseAnswer(lessonId, exerciseId) {
    const {data} = await api.delete(
        API_ROUTES.ADMIN_LESSON_EXERCISE_ANSWER(lessonId, exerciseId)
    );

    return data;
}
