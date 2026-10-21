/**
 * Идентификатор модуля.
 *
 * Backend в разных ответах называет его id или module_id,
 * поэтому единая функция избавляет от расхождений в разных
 * частях админки.
 *
 * @param {object} module модуль
 * @returns {number|null}
 */
export function getModuleId(module) {
    return module?.module_id ?? module?.id ?? null;
}
