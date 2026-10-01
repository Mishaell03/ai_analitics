/**
 * Маски и валидация полей профиля.
 *
 * Формат телефона: +7 (XXX) XXX-XX-XX
 * Формат email:    user@example.com
 */

const PHONE_PREFIX = "+7";

/**
 * Приводит строку к маске +7 (XXX) XXX-XX-XX.
 *
 * Разделители дописываются только после того, как группа набрана
 * целиком. Иначе backspace не работал бы: маска дописывала бы
 * разделитель, который только что удалили, и строка не менялась бы.
 *
 * Пустая строка не получает префикс +7 — иначе поле нельзя было бы
 * очистить целиком.
 */
export function formatPhone(value) {
    const digits = (value || "").replace(/\D/g, "");

    if (!digits) {
        return "";
    }

    // 7 или 8 в начале — российский код, приводим к 7
    let rest = digits;

    if (rest[0] === "7" || rest[0] === "8") {
        rest = rest.slice(1);
    }

    rest = rest.slice(0, 10);

    let result = PHONE_PREFIX;

    if (rest.length) {
        result += ` (${rest.slice(0, 3)}`;
    }

    // Закрываем скобку и открываем следующую группу только если
    // есть что туда положить. Иначе на ровно 3 цифрах остаётся
    // висящая скобка, которую backspace удалит и маска вернёт обратно.
    if (rest.length > 3) {
        result += `) ${rest.slice(3, 6)}`;
    }

    // Дефис ставим только перед следующей цифрой, иначе он висит
    // в конце и backspace по нему не проходит дальше
    if (rest.length > 6) {
        result += `-${rest.slice(6, 8)}`;
    }

    if (rest.length > 8) {
        result += `-${rest.slice(8, 10)}`;
    }

    return result;
}

/**
 * Телефон заполнен полностью: 10 цифр после кода.
 * Пустая строка — валидное значение, поле необязательное.
 */
export function isValidPhone(value) {
    if (!value) {
        return true;
    }

    return (value.match(/\d/g) || []).length === 11;
}

/**
 * Строгая проверка email, символ в символ разбором,
 * чтобы не зависеть от поддержки lookahead в целевых браузерах.
 */
export function isValidEmail(value) {
    if (!value) {
        return true;
    }

    const email = value.trim();

    if (email.length > 254) {
        return false;
    }

    const parts = email.split("@");

    if (parts.length !== 2) {
        return false;
    }

    const [local, domain] = parts;

    if (!local || local.length > 64 || !domain) {
        return false;
    }

    if (/\s/.test(email)) {
        return false;
    }

    if (!/^[A-Za-z0-9._%+-]+$/.test(local)) {
        return false;
    }

    if (local.startsWith(".") || local.endsWith(".") || local.includes("..")) {
        return false;
    }

    const labels = domain.split(".");

    if (labels.length < 2) {
        return false;
    }

    if (labels.some((label) =>
        !label ||
        label.length > 63 ||
        !/^[A-Za-z0-9-]+$/.test(label) ||
        label.startsWith("-") ||
        label.endsWith("-")
    )) {
        return false;
    }

    if (!/^[A-Za-z]{2,}$/.test(labels[labels.length - 1])) {
        return false;
    }

    return true;
}

/**
 * Валидирует все поля профиля разом.
 * Возвращает объект с полями-ключами, где значение — код ошибки.
 */
export function validateProfile({name, phone, email}) {
    const errors = {};

    if (name !== undefined && name.length > 64) {
        errors.name = "tooLong";
    }

    if (!email || !email.trim()) {
        errors.email = "required";
    } else if (!isValidEmail(email)) {
        errors.email = "invalid";
    }

    if (phone && !isValidPhone(phone)) {
        errors.phone = "invalid";
    }

    return errors;
}
