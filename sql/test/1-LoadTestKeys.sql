-- Load test API keys for local testing
-- These keys are only used in containerized local Supabase environments
-- They provide a complete testing stack without complex mocking

-- Test API Keys (following exact production sk_live_XXXX format):
-- sk_live_adm1234567890123456789012345678901234567890123456789012345678901234: Admin permissions
-- sk_live_wrt1234567890123456789012345678901234567890123456789012345678901234: Read/Write permissions  
-- sk_live_red1234567890123456789012345678901234567890123456789012345678901234: Read-only permissions
-- sk_live_ina1234567890123456789012345678901234567890123456789012345678901234: Inactive key for testing

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
    'sk_live_adm1',  -- First 12 chars: sk_live_ + first 4 chars (adm1)
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
    'sk_live_wrt1',  -- First 12 chars: sk_live_ + first 4 chars (wrt1)
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
    'sk_live_red1',  -- First 12 chars: sk_live_ + first 4 chars (red1)
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
    'sk_live_ina1',  -- First 12 chars: sk_live_ + first 4 chars (ina1)
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
-- Admin key: sk_live_adm1234567890123456789012345678901234567890123456789012345678901234
UPDATE api_keys 
SET key_hash = '$2b$12$eant/LlofQvIjsinzrjT7u/R0nMyyM.2p5z.LKPQjUnDz89QJoicG'
WHERE key_prefix = 'sk_live_adm1';

-- Write key: sk_live_wrt1234567890123456789012345678901234567890123456789012345678901234  
UPDATE api_keys 
SET key_hash = '$2b$12$bMcmjT1o/uJ13oG6FGcCjOW18V9SY2QJ4YSEBl4Rz32sm6MOnBQkK'
WHERE key_prefix = 'sk_live_wrt1';

-- Read key: sk_live_red1234567890123456789012345678901234567890123456789012345678901234
UPDATE api_keys 
SET key_hash = '$2b$12$gIt3Hz2D.GQ97CxR0.9FguB5A6OiKVCZZDg6wIb07daGL4.dtUUVu'
WHERE key_prefix = 'sk_live_red1';

-- Inactive key: sk_live_ina1234567890123456789012345678901234567890123456789012345678901234
UPDATE api_keys 
SET key_hash = '$2b$12$uca9WV34iSE5kws2xNSy5OZ9pOTjA3/yOcBsbz9nXPgWzdNLdu9we'
WHERE key_prefix = 'sk_live_ina1';

-- Add some usage statistics to make test data more realistic
UPDATE api_keys 
SET 
    usage_count = 42,
    last_used_at = NOW() - INTERVAL '1 hour'
WHERE key_prefix = 'sk_live_adm1';

UPDATE api_keys 
SET 
    usage_count = 18, 
    last_used_at = NOW() - INTERVAL '30 minutes'
WHERE key_prefix = 'sk_live_wrt1';

UPDATE api_keys
SET
    usage_count = 7,
    last_used_at = NOW() - INTERVAL '2 hours'  
WHERE key_prefix = 'sk_live_red1';

-- Inactive key has no recent usage
UPDATE api_keys
SET
    usage_count = 156,
    last_used_at = NOW() - INTERVAL '30 days'
WHERE key_prefix = 'sk_live_ina1'; 