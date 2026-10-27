/**
 * РЕЕСТР ОТРИСОВАТЕЛЕЙ КАСТОМНЫХ БЛОКОВ
 *
 * Сервис разбирает кастомный блок в данные, компонент — показывает
 * его. Чтобы поддержать свой тип блока (тест, видео, задание),
 * достаточно зарегистрировать его отрисовщик:
 *
 *     registerCustomBlockRenderer("test", TestBlock);
 *
 * Отрисовщик получает блок и контекст урока (правильные ответы на
 * задания, подписи интерфейса) и возвращает React-элемент.
 * Если обработчика нет, блок показывается как есть.
 */

const renderers = new Map();

/**
 * Регистрирует отрисовщик типа кастомного блока.
 *
 * @param {string} type тип блока (test, video, ...)
 * @param {Function} renderer React-компонент блока
 * @returns {Function} зарегистрированный отрисовщик
 */
export function registerCustomBlockRenderer(type, renderer) {
    renderers.set(type, renderer);

    return renderer;
}

/**
 * Отрисовщик типа кастомного блока или null.
 *
 * @param {string} type тип блока
 * @returns {Function|null}
 */
export function getCustomBlockRenderer(type) {
    return renderers.get(type) ?? null;
}
