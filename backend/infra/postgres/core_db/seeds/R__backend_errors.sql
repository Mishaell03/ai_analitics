-- ошибки
INSERT INTO backend_errors (code, http_status)
VALUES
    ('AUTH_PROVIDER_NOT_FOUND', 400),
    ('EMAIL_ALREADY_EXISTS', 409),
    ('REGISTRATION_FAILED', 400),
    ('INVALID_SESSION', 401),
    ('USER_NOT_FOUND', 404),
    ('USER_BLOCKED', 403),
    ('ADMIN_ACCESS_REQUIRED', 403),
    ('INCORRECT_AUTH_METHOD', 400),
    ('LOGIN_FAILED', 401),
    ('COURSE_NOT_FOUND', 404),
    ('MODULE_NOT_FOUND', 404),
    ('LESSON_NOT_FOUND', 404),
    ('COURSE_ALREADY_ENROLLED', 409),
    ('COURSE_NOT_ENROLLED', 404),
    ('INVALID_PHONE_FORMAT', 422),
    ('PHONE_ALREADY_EXISTS', 409),
    ('CONSENT_REQUIRED', 422),
    ('UPDATE_ME_FAILED', 409)
ON CONFLICT (code) DO NOTHING;

-- локализации ошибок
INSERT INTO backend_errors_localization (code, language, message)
VALUES
    ('AUTH_PROVIDER_NOT_FOUND', 'en', 'This login method is temporarily unavailable'),
    ('AUTH_PROVIDER_NOT_FOUND', 'ru', 'Данный вариант входа временно недоступен'),

    ('EMAIL_ALREADY_EXISTS', 'en', 'Email address already exists'),
    ('EMAIL_ALREADY_EXISTS', 'ru', 'Данный адрес электронной почты уже зарегистрирован'),

    ('REGISTRATION_FAILED', 'en', 'Registration failed'),
    ('REGISTRATION_FAILED', 'ru', 'Не удалось зарегистрировать пользователя'),

     ('INVALID_SESSION', 'en', 'Invalid session'),
    ('INVALID_SESSION', 'ru', 'Недействительная сессия'),

    ('USER_NOT_FOUND', 'en', 'User not found'),
    ('USER_NOT_FOUND', 'ru', 'Пользователь не найден'),

    ('USER_BLOCKED', 'en', 'User is blocked'),
    ('USER_BLOCKED', 'ru', 'Пользователь заблокирован'),

    ('ADMIN_ACCESS_REQUIRED', 'en', 'Admin access required'),
    ('ADMIN_ACCESS_REQUIRED', 'ru', 'Требуются права администратора'),

    ('INCORRECT_AUTH_METHOD', 'en', 'Incorrect authentication method'),
    ('INCORRECT_AUTH_METHOD', 'ru', 'Неверный способ аутентификации'),

    ('LOGIN_FAILED', 'en', 'Login failed'),
    ('LOGIN_FAILED', 'ru', 'Не удалось выполнить вход'),

    ('COURSE_NOT_FOUND', 'en', 'Course not found'),
    ('COURSE_NOT_FOUND', 'ru', 'Курс не найден'),

    ('MODULE_NOT_FOUND', 'en', 'Module not found'),
    ('MODULE_NOT_FOUND', 'ru', 'Модуль не найден'),

    ('LESSON_NOT_FOUND', 'en', 'Lesson not found'),
    ('LESSON_NOT_FOUND', 'ru', 'Урок не найден'),

    ('COURSE_ALREADY_ENROLLED', 'en', 'You are already enrolled in this course'),
    ('COURSE_ALREADY_ENROLLED', 'ru', 'Вы уже записаны на этот курс'),

    ('COURSE_NOT_ENROLLED', 'en', 'You are not enrolled in this course'),
    ('COURSE_NOT_ENROLLED', 'ru', 'Вы не записаны на этот курс'),

    ('INVALID_PHONE_FORMAT', 'en', 'Invalid phone format. Expected +7 (XXX) XXX-XX-XX'),
    ('INVALID_PHONE_FORMAT', 'ru', 'Неверный формат телефона. Ожидается +7 (XXX) XXX-XX-XX'),

    ('PHONE_ALREADY_EXISTS', 'en', 'Phone number already exists'),
    ('PHONE_ALREADY_EXISTS', 'ru', 'Данный номер телефона уже зарегистрирован'),

    ('UPDATE_ME_FAILED', 'en', 'Failed to update profile. Please try again'),
    ('UPDATE_ME_FAILED', 'ru', 'Не удалось обновить профиль. Попробуйте ещё раз'),

    ('CONSENT_REQUIRED', 'en', 'You must accept the personal data processing consent'),
    ('CONSENT_REQUIRED', 'ru', 'Необходимо согласие на обработку персональных данных')
ON CONFLICT (code, language) DO NOTHING;