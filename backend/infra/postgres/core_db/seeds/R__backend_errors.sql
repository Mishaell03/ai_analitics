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
    ('COURSE_NOT_PUBLISHED', 404),
    ('MODULE_NOT_PUBLISHED', 404),
    ('LESSON_NOT_PUBLISHED', 404),
    ('COURSE_ALREADY_ENROLLED', 409),
    ('COURSE_NOT_ENROLLED', 404),
    ('COURSE_ACCESS_REQUIRED', 403),
    ('LESSON_CONTENT_NOT_FOUND', 404),
    ('INVALID_COURSE_SLUG', 409),
    ('COURSE_IMAGE_NOT_FOUND', 404),
    ('MEDIA_FILE_NOT_FOUND', 404),
    ('MEDIA_FILE_TOO_LARGE', 413),
    ('MEDIA_FILE_TYPE_NOT_ALLOWED', 415),
    ('MEDIA_FILE_CORRUPTED', 422),
    ('MEDIA_IMAGE_RESOLUTION_TOO_LARGE', 422),
    ('MEDIA_VIDEO_CODEC_NOT_SUPPORTED', 415),
    ('MEDIA_VIDEO_RESOLUTION_TOO_LARGE', 422),
    ('EXERCISE_ANSWER_NOT_FOUND', 404),
    ('INVALID_PHONE_FORMAT', 422),
    ('PHONE_ALREADY_EXISTS', 409),
    ('CONSENT_REQUIRED', 422),
    ('UPDATE_ME_FAILED', 409),
    ('CANNOT_BLOCK_SELF', 409),
    ('USER_BLOCK_FAILED', 409)
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

    ('COURSE_NOT_PUBLISHED', 'en', 'Course is not published'),
    ('COURSE_NOT_PUBLISHED', 'ru', 'Курс не опубликован'),

    ('MODULE_NOT_PUBLISHED', 'en', 'Module is not published'),
    ('MODULE_NOT_PUBLISHED', 'ru', 'Модуль не опубликован'),

    ('LESSON_NOT_PUBLISHED', 'en', 'Lesson is not published'),
    ('LESSON_NOT_PUBLISHED', 'ru', 'Урок не опубликован'),

    ('COURSE_ALREADY_ENROLLED', 'en', 'You are already enrolled in this course'),
    ('COURSE_ALREADY_ENROLLED', 'ru', 'Вы уже записаны на этот курс'),

    ('COURSE_NOT_ENROLLED', 'en', 'You are not enrolled in this course'),
    ('COURSE_NOT_ENROLLED', 'ru', 'Вы не записаны на этот курс'),

    ('COURSE_ACCESS_REQUIRED', 'en', 'You are not enrolled in this course'),
    ('COURSE_ACCESS_REQUIRED', 'ru', 'Вы не записаны на этот курс'),

    ('LESSON_CONTENT_NOT_FOUND', 'en', 'Lesson content not found'),
    ('LESSON_CONTENT_NOT_FOUND', 'ru', 'Содержимое урока не найдено'),

    ('INVALID_COURSE_SLUG', 'en', 'Course slug cannot be used to store lesson files'),
    ('INVALID_COURSE_SLUG', 'ru', 'Slug курса нельзя использовать для хранения файлов урока'),

    ('COURSE_IMAGE_NOT_FOUND', 'en', 'Course image not found'),
    ('COURSE_IMAGE_NOT_FOUND', 'ru', 'Обложка курса не найдена'),

    ('MEDIA_FILE_NOT_FOUND', 'en', 'Media file not found'),
    ('MEDIA_FILE_NOT_FOUND', 'ru', 'Медиафайл не найден'),

    ('MEDIA_FILE_TOO_LARGE', 'en', 'File is larger than allowed'),
    ('MEDIA_FILE_TOO_LARGE', 'ru', 'Файл больше допустимого размера'),

    ('MEDIA_FILE_TYPE_NOT_ALLOWED', 'en', 'This file type is not supported'),
    ('MEDIA_FILE_TYPE_NOT_ALLOWED', 'ru', 'Такой тип файла не поддерживается'),

    ('MEDIA_FILE_CORRUPTED', 'en', 'Failed to read the file'),
    ('MEDIA_FILE_CORRUPTED', 'ru', 'Не удалось прочитать файл'),

    ('MEDIA_IMAGE_RESOLUTION_TOO_LARGE', 'en', 'Image resolution is too large'),
    ('MEDIA_IMAGE_RESOLUTION_TOO_LARGE', 'ru', 'Разрешение изображения слишком большое'),

    ('MEDIA_VIDEO_CODEC_NOT_SUPPORTED', 'en', 'Video codec is not supported, use H.264 with AAC'),
    ('MEDIA_VIDEO_CODEC_NOT_SUPPORTED', 'ru', 'Кодек видео не поддерживается, используйте H.264 с AAC'),

    ('MEDIA_VIDEO_RESOLUTION_TOO_LARGE', 'en', 'Video resolution is too large'),
    ('MEDIA_VIDEO_RESOLUTION_TOO_LARGE', 'ru', 'Разрешение видео слишком большое'),

    ('EXERCISE_ANSWER_NOT_FOUND', 'en', 'Correct answer for the exercise not found'),
    ('EXERCISE_ANSWER_NOT_FOUND', 'ru', 'Правильный ответ на задание не найден'),

    ('INVALID_PHONE_FORMAT', 'en', 'Invalid phone format. Expected +7 (XXX) XXX-XX-XX'),
    ('INVALID_PHONE_FORMAT', 'ru', 'Неверный формат телефона. Ожидается +7 (XXX) XXX-XX-XX'),

    ('PHONE_ALREADY_EXISTS', 'en', 'Phone number already exists'),
    ('PHONE_ALREADY_EXISTS', 'ru', 'Данный номер телефона уже зарегистрирован'),

    ('UPDATE_ME_FAILED', 'en', 'Failed to update profile. Please try again'),
    ('UPDATE_ME_FAILED', 'ru', 'Не удалось обновить профиль. Попробуйте ещё раз'),

    ('CONSENT_REQUIRED', 'en', 'You must accept the personal data processing consent'),
    ('CONSENT_REQUIRED', 'ru', 'Необходимо согласие на обработку персональных данных'),

    ('CANNOT_BLOCK_SELF', 'en', 'You cannot block yourself'),
    ('CANNOT_BLOCK_SELF', 'ru', 'Нельзя заблокировать самого себя'),

    ('USER_BLOCK_FAILED', 'en', 'Failed to change the block status. Please try again'),
    ('USER_BLOCK_FAILED', 'ru', 'Не удалось изменить статус блокировки. Попробуйте ещё раз')
ON CONFLICT (code, language) DO NOTHING;