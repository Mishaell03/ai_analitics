-- Тестовые учётные записи: без сессий, зачислений и прогресса.
-- Пароли равны полному email (user1@example.com ... user11@example.com).
-- Такие предсказуемые пароли не подходят для публичного продакшена.
-- Согласие ниже — предзаполненные данные, не журнал реального действия пользователя.
-- example.com и неиспользуемый телефонный код +7 000 — тестовые контакты.
-- При повторном запуске существующие email пропускаются: пароли,
-- аватары и согласия существующих пользователей не меняются.
INSERT INTO providers (code, name)
VALUES ('pass', 'Password')
ON CONFLICT (code) DO NOTHING;

WITH new_users AS (
    INSERT INTO users (name, phone, email, img, is_default_img, is_admin, is_blocked)
    SELECT
        name,
        '+7000' || lpad(floor(random() * 100000)::text, 5, '0')
            || lpad(number::text, 2, '0'),
        'user' || number || '@example.com',
        img,
        TRUE,
        FALSE,
        FALSE
    FROM (VALUES
        (1, 'Татьяна Щербакова', 'user3'),
        (2, 'Екатерина Шаврина', 'user6'),
        (3, 'Дмитрий Букачев', 'user2'),
        (4, 'Лидия Евсеенкова', 'user8'),
        (5, 'Ирина Ефимова', 'user3'),
        (6, 'Никита Ирушкин', 'user4'),
        (7, 'Даниил Козлов', 'user7'),
        (8, 'Татьяна Кудрявцева', 'user6'),
        (9, 'Ирина Почтенная', 'user8'),
        (10, 'Алексей Соколов', 'user9'),
        (11, 'Анжелика Трофимова', 'user3')
    ) AS accounts(number, name, img)
    ON CONFLICT (email) DO NOTHING
    RETURNING user_id, email
), new_consents AS (
    INSERT INTO users_consents (user_id, consent_code, is_accepted, policy_version)
    SELECT user_id, 'PERSONAL_DATA', TRUE, '1.0'
    FROM new_users
    RETURNING consent_id
)

INSERT INTO user_auth_methods (user_id, provider, password_hash)
SELECT u.user_id, 'pass', accounts.password_hash
FROM (VALUES
    ('user1@example.com', '$argon2id$v=19$m=65536,t=3,p=4$3OMaXgzX/e0Q7WXQiwefUQ$MDCV1nh8hP2N+vsMFwR1+hIkWxHzst1pZDajXovYCr8'),
    ('user2@example.com', '$argon2id$v=19$m=65536,t=3,p=4$E4hvKZjIcTr7BwooR/NmEg$2z2iCR2dxTq8bTbcnoMPLnpnOE9VwDkSXNlAN3j21kE'),
    ('user3@example.com', '$argon2id$v=19$m=65536,t=3,p=4$xSxMefaZ4w58JTUnKy+rlQ$cR9j2G/FWioxM2s7baUJAdn/9b/Z8TSIleSqlSZLkkc'),
    ('user4@example.com', '$argon2id$v=19$m=65536,t=3,p=4$kjbfZP5CymUIJTGr+fCckA$0/ZphDDcuE3aFROdkLfAoc2AWVHudHSKjVCGhLzlwN4'),
    ('user5@example.com', '$argon2id$v=19$m=65536,t=3,p=4$lTMsniBwmtRKpLrNnJX3IA$LDpXObhRUdvzT3Wvxbmf2Q6PuwSB1NmxvEUiG8Q5McA'),
    ('user6@example.com', '$argon2id$v=19$m=65536,t=3,p=4$8XEoAui9C3F/oMZiYaWuJQ$YVzTEjNLDRmlUvVyMENx15CdFVA3Famku+Y/Bhzw7UQ'),
    ('user7@example.com', '$argon2id$v=19$m=65536,t=3,p=4$dmzYed0J1t49XDPp90BpRA$GfQjT+TWsAYgLMfVu/xwPPbN+qIFsfF6Yp1qmrq3A3g'),
    ('user8@example.com', '$argon2id$v=19$m=65536,t=3,p=4$rUjBjoQK8UQikCw6/KN8Qg$7obsHj/NvdI6tS20rmYjMv4G6I33Won9SG9ixpJ+Hw0'),
    ('user9@example.com', '$argon2id$v=19$m=65536,t=3,p=4$QkIVt6g40rEI8IxPr9mu1w$T7qfU40211IezoVs4jlPEdXxyVKCYdoLLqj5BxcFA7k'),
    ('user10@example.com', '$argon2id$v=19$m=65536,t=3,p=4$JBldsKNL6XUUZ9txC0cLoQ$2zFxrM3GKA4fkXpjQCZdC+RkNJj7eCxh8GHhurk9Gyc'),
    ('user11@example.com', '$argon2id$v=19$m=65536,t=3,p=4$F7eU1K2UKUPQdyVx7q/kAA$7mNZs+NNT6z1Q8vtieRQRnA+/aEnkhh9i9Q/SVC7Mas')
) AS accounts(email, password_hash)
JOIN new_users AS u ON u.email = accounts.email;
