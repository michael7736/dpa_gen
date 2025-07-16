-- 创建默认用户
-- 密码是 'default123' 的 bcrypt hash
INSERT INTO users (id, email, username, full_name, hashed_password, is_active, is_superuser, is_deleted, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'default@dpa.ai',
    'default',
    'Default User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGhEdRpLu4K',
    true,
    false,
    false,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;