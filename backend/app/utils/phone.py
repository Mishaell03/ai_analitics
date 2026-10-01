import re

# допустимые символы в маске: +7 (999) 000-00-01
PHONE_MASK_PATTERN = re.compile(r"^\+?[\d\s()\-]+$")

# 11 цифр: код страны 7/8 + десять цифр номера
PHONE_DIGITS_PATTERN = re.compile(r"^[78]\d{10}$")


def normalize_phone(value: str | None) -> str | None:
    """Приводит телефон к каноническому виду +7XXXXXXXXXX.

    Принимает маску (+7 (999) 000-00-01), а также 8XXXXXXXXXX и 7XXXXXXXXXX.
    Пустое значение приводится к None, чтобы поле можно было очистить.
    Бросает ValueError, если формат не соответствует маске.
    """

    if value is None:
        return None

    phone = value.strip()

    if not phone:
        return None

    if not PHONE_MASK_PATTERN.match(phone):
        raise ValueError("INVALID_PHONE_FORMAT")

    digits = "".join(re.findall(r"\d", phone))

    if not PHONE_DIGITS_PATTERN.match(digits):
        raise ValueError("INVALID_PHONE_FORMAT")

    return f"+7{digits[1:]}"