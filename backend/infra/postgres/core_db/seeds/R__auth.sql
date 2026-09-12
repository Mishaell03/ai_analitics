INSERT INTO providers (code, name)
VALUES
    ('ya', 'Yandex'),
    ('pass', 'Password');


-- USERS
INSERT INTO users (name, phone, email, img, is_default_img, is_admin, is_blocked) VALUES
(
    'Алексей Морозов',
    '+79990000001',
    'alexey.morozov@example.com',
    'user1',
    TRUE,
    FALSE,
    FALSE
),
(
    'Мария Волкова',
    '+79990000002',
    'maria.volkova@example.com',
    'user2',
    TRUE,
    FALSE,
    FALSE
),
(
    'Дмитрий Соколов',
    '+79990000003',
    'dmitry.sokolov@example.com',
    'user3',
    TRUE,
    TRUE,
    FALSE
);


-- AUTH METHODS
INSERT INTO user_auth_methods (user_id, provider, password_hash ) VALUES (
    (SELECT user_id FROM users WHERE email = 'alexey.morozov@example.com'),
    'pass',
    '$argon2id$v=19$m=65536,t=3,p=4$qtwi8fCEWYrwll3xHlZpjw$x2DepSmZU3SEKs0oSpOIHvua/8nXH83oi2APvGahs8s'
),
(
    (SELECT user_id FROM users WHERE email = 'maria.volkova@example.com'),
    'pass',
    '$argon2id$v=19$m=65536,t=3,p=4$/XJTjWQpdaQA9sgN2sBZWA$gmA+gTX0jX3qNkbZL62Fss/sVQe5i4zrPRbACiKBzr4'
),
(
    (SELECT user_id FROM users WHERE email = 'dmitry.sokolov@example.com'),
    'pass',
    '$argon2id$v=19$m=65536,t=3,p=4$J4IF7Ep1UviiPB+q911XtA$lE837XPEfkhiWWaVmEybZp9sCIGwIue5xnQFw5ZjVV0'
);


-- SESSIONS
INSERT INTO users_sessions (device_id, user_id, session, ip, language, provider, platform, device_name, expires_at ) VALUES
(
    'seed-device-alexey',
    (SELECT user_id FROM users WHERE email = 'alexey.morozov@example.com'),
    'seed-session-alexey-2026',
    '127.0.0.1',
    'RU',
    'pass',
    'web',
    'Seed Browser',
    '2099-12-31 23:59:59+00'
),
(
    'seed-device-maria',
    (SELECT user_id FROM users WHERE email = 'maria.volkova@example.com'),
    'seed-session-maria-2026',
    '127.0.0.1',
    'RU',
    'pass',
    'web',
    'Seed Browser',
    '2099-12-31 23:59:59+00'
),
(
    'seed-device-dmitry',
    (SELECT user_id FROM users WHERE email = 'dmitry.sokolov@example.com'),
    'seed-session-dmitry-2026',
    '127.0.0.1',
    'RU',
    'pass',
    'web',
    'Seed Browser',
    '2099-12-31 23:59:59+00'
);
