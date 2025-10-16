-- Load test API keys for local testing
-- These keys are only used in containerized local Supabase environments
-- They provide a complete testing stack without complex mocking

-- Test API Keys (using test_key_ prefix to avoid GitHub secret scanning):
-- test_key_admin_1234567890abcdef1234567890abcdef1234567890abcdef123456789: Admin permissions
-- test_key_write_1234567890abcdef1234567890abcdef1234567890abcdef123456789: Read/Write permissions  
-- test_key_read_1234567890abcdef1234567890abcdef1234567890abcdef1234567890: Read-only permissions
-- test_key_inactive_1234567890abcdef1234567890abcdef1234567890abcdef12345: Inactive key for testing

INSERT INTO api_keys (
    id,
    key_hash,
    key_prefix,
    name,
    description,
    client_name,
    is_active,
    permissions_scope,
    rate_limit_rpm,
    allowed_ips,
    created_at,
    updated_at
) VALUES
-- Admin test key
(
    '00000000-1111-2222-3333-444444444444',
    '$2b$12$placeholder_admin_hash_will_be_generated_automatically_when_loaded',
    'test_key_adm',  -- First 12 chars of test_key_admin_...
    'Test Admin Key 11112222-3333-4444', 
    'Admin API key for testing complete workflows',
    'test-admin-client-' || '11112222-3333-4444',
    true,
    ARRAY['admin'],
    1000,
    ARRAY['127.0.0.1', '::1', '0.0.0.0/0', 'testclient'],
    NOW(),
    NOW()
),
-- Write test key
(
    '00000000-2222-3333-4444-555555555555',
    '$2b$12$placeholder_write_hash_will_be_generated_automatically_when_loaded',
    'test_key_wri',  -- First 12 chars of test_key_write_...
    'Test Write Key 22223333-4444-5555',
    'Read/Write API key for testing normal operations', 
    'test-write-client-' || '22223333-4444-5555',
    true,
    ARRAY['read', 'write'],
    500,
    ARRAY['127.0.0.1', '::1', '0.0.0.0/0', 'testclient'],
    NOW(),
    NOW()
),
-- Read-only test key
(
    '00000000-3333-4444-5555-666666666666',
    '$2b$12$placeholder_read_hash_will_be_generated_automatically_when_loaded',
    'test_key_rea',  -- First 12 chars of test_key_read_...
    'Test Read Key 33344444-5555-6666',
    'Read-only API key for testing restricted operations',
    'test-read-client-' || '33344444-5555-6666', 
    true,
    ARRAY['read'],
    100,
    ARRAY['127.0.0.1', '::1', '0.0.0.0/0', 'testclient'],
    NOW(),
    NOW()
),
-- Inactive test key
(
    '00000000-4444-5555-6666-777777777777',
    '$2b$12$placeholder_inactive_hash_will_be_generated_automatically_when_loaded',
    'test_key_ina',  -- First 12 chars of test_key_inactive_...
    'Test Inactive Key 44445555-6666-7777',
    'Inactive API key for testing revocation scenarios',
    'test-inactive-client-' || '44445555-6666-7777',
    false,  -- Inactive
    ARRAY['read'],
    100,
    ARRAY['127.0.0.1', '::1', 'testclient'],
    NOW(),
    NOW()
);

-- Generate proper bcrypt hashes for the test keys
-- Admin key: test_key_admin_1234567890abcdef1234567890abcdef1234567890abcdef123456789
UPDATE api_keys 
SET key_hash = '$2b$12$dNTl/ZkVEL60kCx5y.GhB.5S.x6O2PzNMuctEpKWgzb8vxkcwMwjy'
WHERE key_prefix = 'test_key_adm';

-- Write key: test_key_write_1234567890abcdef1234567890abcdef1234567890abcdef123456789  
UPDATE api_keys 
SET key_hash = '$2b$12$pmwgfAAOuOl5zkEQHJz0FOOnNTHG88PYK8VFl0jDaSncZbm2xX/QO'
WHERE key_prefix = 'test_key_wri';

-- Read key: test_key_read_1234567890abcdef1234567890abcdef1234567890abcdef1234567890
UPDATE api_keys 
SET key_hash = '$2b$12$tJT10fcvYqOlxbtcyd54puSgIJWM1gEGiPJgCsZ00NHDjv3Al.OK.'
WHERE key_prefix = 'test_key_rea';

-- Inactive key: test_key_inactive_1234567890abcdef1234567890abcdef1234567890abcdef12345
UPDATE api_keys 
SET key_hash = '$2b$12$A1IZmresBTIFd87sVFOYAeuIPHhXic81JC5PCDxS1jlNVmfIschGO'
WHERE key_prefix = 'test_key_ina';

-- Add some usage statistics to make test data more realistic
UPDATE api_keys 
SET 
    usage_count = 42,
    last_used_at = NOW() - INTERVAL '1 hour'
WHERE key_prefix = 'test_key_adm';

UPDATE api_keys 
SET 
    usage_count = 18, 
    last_used_at = NOW() - INTERVAL '30 minutes'
WHERE key_prefix = 'test_key_wri';

UPDATE api_keys
SET
    usage_count = 7,
    last_used_at = NOW() - INTERVAL '2 hours'  
WHERE key_prefix = 'test_key_rea';

-- Inactive key has no recent usage
UPDATE api_keys
SET
    usage_count = 156,
    last_used_at = NOW() - INTERVAL '30 days'
WHERE key_prefix = 'test_key_ina'; 