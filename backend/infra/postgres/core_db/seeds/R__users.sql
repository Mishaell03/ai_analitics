INSERT INTO users (
    name,
    phone,
    email,
    img,
    is_default_img,
    is_admin,
    is_blocked
) VALUES
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