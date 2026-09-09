-- ошибки
INSERT INTO backend_errors (code, http_status)
VALUES
    ('AUTH_PROVIDER_NOT_FOUND', 400),
    ('EMAIL_ALREADY_EXISTS', 409),
    ('REGISTRATION_FAILED', 400)
ON CONFLICT (code) DO NOTHING;

-- локализации ошибок
INSERT INTO backend_errors_localization (code, language, message)
VALUES
    ('AUTH_PROVIDER_NOT_FOUND', 'en', 'This login method is temporarily unavailable'),
    ('AUTH_PROVIDER_NOT_FOUND', 'ru', 'Данный вариант входа временно недоступен'),

    ('EMAIL_ALREADY_EXISTS', 'en', 'Email address already exists'),
    ('EMAIL_ALREADY_EXISTS', 'ru', 'Данный адрес электронной почты уже зарегистрирован'),

    ('REGISTRATION_FAILED', 'en', 'Registration failed'),
    ('REGISTRATION_FAILED', 'ru', 'Не удалось зарегистрировать пользователя')
ON CONFLICT (code, language) DO NOTHING;