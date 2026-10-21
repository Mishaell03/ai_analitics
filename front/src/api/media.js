import {api, formApi} from "@/api/axios.js";
import {API_ROUTES} from "@/api/routes.js";

/**
 * API-КЛИЕНТ МЕДИАФАЙЛОВ
 *
 * Здесь только запросы: адреса живут в API_ROUTES, а правила файлов
 * — в services/media.js. Компоненты не знают ни про multipart,
 * ни про прогресс загрузки.
 */

/**
 * Процент загруженного файла.
 *
 * @param {object} event событие прогресса axios
 * @returns {number|null}
 */
function toProgress(event) {
    if (!event?.total) {
        return null;
    }

    return Math.min(Math.round((event.loaded / event.total) * 100), 100);
}

/**
 * Загружает файл с отчётом о прогрессе.
 *
 * @param {string} url адрес запроса
 * @param {File} file файл
 * @param {object} options прогресс и отмена запроса
 * @returns {Promise<object>}
 */
async function uploadFile(url, file, {onProgress, signal} = {}) {
    const formData = new FormData();

    formData.append("file", file);

    const {data} = await formApi.post(url, formData, {
        signal,
        onUploadProgress: (event) => onProgress?.(toProgress(event)),
    });

    return data;
}


/* ---------- обложка курса ---------- */

/**
 * Обложка курса вместе с временной ссылкой.
 *
 * @param {string} courseSlug slug курса
 * @returns {Promise<object>}
 */
export async function getCourseImage(courseSlug) {
    const {data} = await api.get(API_ROUTES.ADMIN_COURSE_IMAGE(courseSlug));

    return data;
}

/**
 * Загружает обложку курса (или заменяет текущую).
 *
 * @param {string} courseSlug slug курса
 * @param {File} file изображение
 * @param {object} options прогресс и отмена запроса
 * @returns {Promise<object>}
 */
export async function uploadCourseImage(courseSlug, file, options) {
    return uploadFile(API_ROUTES.ADMIN_COURSE_IMAGE(courseSlug), file, options);
}

/**
 * Удаляет обложку курса.
 *
 * @param {string} courseSlug slug курса
 * @returns {Promise<object>}
 */
export async function deleteCourseImage(courseSlug) {
    const {data} = await api.delete(API_ROUTES.ADMIN_COURSE_IMAGE(courseSlug));

    return data;
}


/* ---------- медиафайлы урока ---------- */

/**
 * Медиафайлы урока.
 *
 * @param {string} courseSlug slug курса
 * @param {number} moduleId id модуля
 * @param {number} lessonId id урока
 * @param {object} params страница и размер
 * @returns {Promise<object>}
 */
export async function listLessonMedia(courseSlug, moduleId, lessonId, {page = 1, pageSize = 100} = {}) {
    const {data} = await api.get(
        API_ROUTES.ADMIN_LESSON_MEDIA(courseSlug, moduleId, lessonId),
        {params: {page, page_size: pageSize}}
    );

    return data;
}

/**
 * Загружает файл в урок.
 *
 * @param {string} courseSlug slug курса
 * @param {number} moduleId id модуля
 * @param {number} lessonId id урока
 * @param {File} file изображение или видео
 * @param {object} options прогресс и отмена запроса
 * @returns {Promise<object>}
 */
export async function uploadLessonMedia(courseSlug, moduleId, lessonId, file, options) {
    return uploadFile(
        API_ROUTES.ADMIN_LESSON_MEDIA(courseSlug, moduleId, lessonId),
        file,
        options
    );
}

/**
 * Убирает файл из урока.
 *
 * Если файл больше не используется другими уроками, backend удаляет
 * его вместе с объектом в хранилище.
 *
 * @param {number} lessonId id урока
 * @param {string} mediaKey идентификатор файла
 * @returns {Promise<object>}
 */
export async function deleteLessonMedia(lessonId, mediaKey) {
    const {data} = await api.delete(API_ROUTES.ADMIN_LESSON_MEDIA_ITEM(lessonId, mediaKey));

    return data;
}

/**
 * Новая временная ссылка на файл.
 *
 * Ссылки живут недолго, поэтому её можно запросить в любой момент.
 *
 * @param {string} mediaKey идентификатор файла
 * @returns {Promise<object>}
 */
export async function refreshMediaUrl(mediaKey) {
    const {data} = await api.post(API_ROUTES.ADMIN_MEDIA_URL(mediaKey));

    return data;
}
