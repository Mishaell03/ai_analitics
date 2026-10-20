/**
 * Форматирование значений, приходящих с API.
 *
 * Числа: 12 345
 * Даты:  12 марта 2026, 14:30
 */

const LOCALE = "ru-RU";

const DASH = "—";

const numberFormatter = new Intl.NumberFormat(LOCALE);

const dateFormatter = new Intl.DateTimeFormat(LOCALE, {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
});

/**
 * Разделяет разряды, null и нечисловые значения приводит к нулю.
 */
export function formatNumber(value) {
    return numberFormatter.format(Number(value) || 0);
}

/**
 * Дата и время в русском формате.
 * Некорректная или пустая дата возвращается как прочерк.
 */
export function formatDateTime(value, fallback = DASH) {
    if (!value) {
        return fallback;
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return fallback;
    }

    return dateFormatter.format(date);
}

/**
 * Размер файла в человекочитаемом виде: 12,3 КБ.
 */
export function formatBytes(value) {
    const size = Number(value);

    if (!Number.isFinite(size) || size < 0) {
        return DASH;
    }

    if (size < 1024) {
        return `${size} Б`;
    }

    if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1).replace(".", ",")} КБ`;
    }

    return `${(size / (1024 * 1024)).toFixed(1).replace(".", ",")} МБ`;
}
