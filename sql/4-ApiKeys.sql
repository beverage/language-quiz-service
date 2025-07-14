-- ===== API KEYS SCHEMA FOR SUPABASE =====
-- Production-quality API key authentication system

-- Drop table if exists (for development)
-- DROP TABLE IF EXISTS api_keys CASCADE;

-- API Keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core authentication fields
    key_hash TEXT NOT NULL UNIQUE, -- Hashed version of the API key (never store plain text)
    key_prefix TEXT NOT NULL, -- First 12 chars for identification (e.g., "sk_live_abcd")
    
    -- Metadata
    name TEXT NOT NULL, -- Human-readable name (e.g., "Personal Website", "Mobile App")
    description TEXT, -- Optional description
    client_name TEXT, -- Client application name
    
    -- Status and permissions
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    permissions_scope TEXT[] DEFAULT ARRAY['read'], -- Future: ['read', 'write', 'admin']
    
    -- Security
    allowed_ips TEXT[], -- Optional IP allowlist (CIDR notation supported)
    
    -- Usage tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count BIGINT DEFAULT 0,
    
    -- Rate limiting (requests per minute)
    rate_limit_rpm INTEGER DEFAULT 100,
    
    -- Constraints
    CHECK (name != ''),
    CHECK (key_hash != ''),
    CHECK (key_prefix != ''),
    CHECK (rate_limit_rpm > 0)
);

-- Indexes for performance
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash); -- Primary lookup
CREATE INDEX idx_api_keys_active ON api_keys(is_active); -- Active keys only
CREATE INDEX idx_api_keys_created_at ON api_keys(created_at); -- Sorting
CREATE INDEX idx_api_keys_last_used ON api_keys(last_used_at); -- Usage analytics

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

CREATE TRIGGER api_keys_updated_at_trigger
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_api_keys_updated_at();

-- Function to atomically increment usage count and update timestamp
CREATE OR REPLACE FUNCTION increment_api_key_usage(key_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE api_keys 
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = key_id;
END;
$$ LANGUAGE plpgsql;

-- RLS (Row Level Security) - basic setup
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (adjust based on your admin auth requirements)
CREATE POLICY api_keys_select_policy ON api_keys
    FOR SELECT USING (true); -- Adjust as needed for admin access

CREATE POLICY api_keys_insert_policy ON api_keys  
    FOR INSERT WITH CHECK (true); -- Adjust as needed

CREATE POLICY api_keys_update_policy ON api_keys
    FOR UPDATE USING (true); -- Adjust as needed

CREATE POLICY api_keys_delete_policy ON api_keys
    FOR DELETE USING (true); -- Adjust as needed

-- Comments for documentation
COMMENT ON TABLE api_keys IS 'API keys for service-to-service authentication';
COMMENT ON COLUMN api_keys.key_hash IS 'Hashed API key using bcrypt - never store plain text';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 12 characters of key for identification (e.g., sk_live_abcd)';
COMMENT ON COLUMN api_keys.permissions_scope IS 'Array of permissions: read, write, admin';
COMMENT ON COLUMN api_keys.allowed_ips IS 'Optional IP allowlist in CIDR notation (e.g., ["192.168.1.0/24", "203.0.113.42/32"])';
COMMENT ON COLUMN api_keys.rate_limit_rpm IS 'Requests per minute limit for this key';
COMMENT ON COLUMN api_keys.usage_count IS 'Total number of requests made with this key';

-- Example insert (for testing - you'll generate this via CLI)
-- INSERT INTO api_keys (key_hash, key_prefix, name, description, client_name, allowed_ips) 
-- VALUES ('$2b$12$example_hash', 'sk_live_abcd', 'Personal Website', 'API access for alexbeverage.com', 'Personal Website', ARRAY['203.0.113.42/32']);