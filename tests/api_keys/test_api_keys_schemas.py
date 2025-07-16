"""Comprehensive tests for API key schemas and utilities."""

from datetime import UTC, datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.api_keys import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyStats,
    ApiKeyUpdate,
    ApiKeyWithPlainText,
    check_ip_allowed,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


@pytest.fixture
def sample_api_key_create_data():
    """Sample data for creating API keys."""
    return {
        "name": "Test API Key",
        "description": "A test API key for unit testing",
        "client_name": "Test Client",
        "permissions_scope": ["read"],
        "rate_limit_rpm": 100,
        "allowed_ips": ["192.168.1.0/24", "203.0.113.42/32"],
    }


@pytest.fixture
def sample_api_key_data():
    """Sample data for complete API key objects."""
    return {
        "id": uuid4(),
        "key_hash": "$2b$12$example_hash_here",
        "key_prefix": "sk_live_abcd",
        "name": "Test API Key",
        "description": "A test API key",
        "client_name": "Test Client",
        "is_active": True,
        "permissions_scope": ["read"],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "last_used_at": None,
        "usage_count": 0,
        "rate_limit_rpm": 100,
        "allowed_ips": ["192.168.1.0/24"],
    }


class TestApiKeyCreate:
    """Test ApiKeyCreate schema validation."""

    def test_valid_api_key_create(self, sample_api_key_create_data):
        """Test creating valid API key with all fields."""
        key_create = ApiKeyCreate(**sample_api_key_create_data)

        assert key_create.name == "Test API Key"
        assert key_create.description == "A test API key for unit testing"
        assert key_create.client_name == "Test Client"
        assert key_create.permissions_scope == ["read"]
        assert key_create.rate_limit_rpm == 100
        assert key_create.allowed_ips == ["192.168.1.0/24", "203.0.113.42/32"]

    def test_minimal_api_key_create(self):
        """Test creating API key with minimal required fields."""
        key_create = ApiKeyCreate(name="Minimal Key")

        assert key_create.name == "Minimal Key"
        assert key_create.description is None
        assert key_create.client_name is None
        assert key_create.permissions_scope == ["read"]  # default
        assert key_create.rate_limit_rpm == 100  # default
        assert key_create.allowed_ips is None

    def test_name_validation_empty(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCreate(name="")

        # Pydantic v2 uses built-in validation for min_length
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_name_validation_whitespace(self):
        """Test that whitespace-only names are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCreate(name="   ")

        assert "Name cannot be empty" in str(exc_info.value)

    def test_name_trimming(self):
        """Test that names are trimmed of whitespace."""
        key_create = ApiKeyCreate(name="  Test Key  ")
        assert key_create.name == "Test Key"

    def test_permissions_validation_valid(self):
        """Test valid permissions are accepted."""
        for permission in ["read", "write", "admin"]:
            key_create = ApiKeyCreate(name="Test", permissions_scope=[permission])
            assert key_create.permissions_scope == [permission]

    def test_permissions_validation_invalid(self):
        """Test invalid permissions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCreate(name="Test", permissions_scope=["invalid"])

        assert "Invalid permission: invalid" in str(exc_info.value)

    def test_permissions_validation_mixed(self):
        """Test mixed valid/invalid permissions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCreate(name="Test", permissions_scope=["read", "invalid", "write"])

        assert "Invalid permission: invalid" in str(exc_info.value)

    def test_rate_limit_validation(self):
        """Test rate limit boundaries."""
        # Valid values
        key_create = ApiKeyCreate(name="Test", rate_limit_rpm=1)
        assert key_create.rate_limit_rpm == 1

        key_create = ApiKeyCreate(name="Test", rate_limit_rpm=10000)
        assert key_create.rate_limit_rpm == 10000

        # Invalid values
        with pytest.raises(ValidationError):
            ApiKeyCreate(name="Test", rate_limit_rpm=0)

        with pytest.raises(ValidationError):
            ApiKeyCreate(name="Test", rate_limit_rpm=10001)

    def test_ip_allowlist_validation_valid(self):
        """Test valid IP addresses and CIDR ranges."""
        valid_ips = [
            ["192.168.1.1"],
            ["192.168.1.0/24"],
            ["203.0.113.42/32"],
            ["10.0.0.0/8", "172.16.0.0/12"],
            ["::1", "2001:db8::/32"],  # IPv6
        ]

        for ip_list in valid_ips:
            key_create = ApiKeyCreate(name="Test", allowed_ips=ip_list)
            assert key_create.allowed_ips == ip_list

    def test_ip_allowlist_validation_invalid(self):
        """Test invalid IP addresses are rejected."""
        invalid_ips = [
            ["invalid.ip"],
            ["999.999.999.999"],
            ["192.168.1.0/33"],  # Invalid CIDR
            ["not-an-ip"],
        ]

        for ip_list in invalid_ips:
            with pytest.raises(ValidationError) as exc_info:
                ApiKeyCreate(name="Test", allowed_ips=ip_list)
            assert "Invalid IP address or CIDR notation" in str(exc_info.value)


class TestApiKeyUpdate:
    """Test ApiKeyUpdate schema validation."""

    def test_partial_update(self):
        """Test updating only some fields."""
        update = ApiKeyUpdate(name="Updated Name", is_active=False)

        assert update.name == "Updated Name"
        assert update.is_active is False
        assert update.description is None
        assert update.permissions_scope is None

    def test_name_validation_with_none(self):
        """Test that None names are allowed in updates."""
        update = ApiKeyUpdate(name=None)
        assert update.name is None

    def test_name_validation_empty_in_update(self):
        """Test that empty names are rejected in updates."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyUpdate(name="")

        # Pydantic v2 uses built-in validation for min_length
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_permissions_validation_with_none(self):
        """Test that None permissions are allowed in updates."""
        update = ApiKeyUpdate(permissions_scope=None)
        assert update.permissions_scope is None

    def test_permissions_validation_in_update(self):
        """Test permissions validation works in updates."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyUpdate(permissions_scope=["invalid"])

        assert "Invalid permission: invalid" in str(exc_info.value)

    def test_ip_allowlist_validation_in_update(self):
        """Test IP allowlist validation works in updates."""
        with pytest.raises(ValidationError) as exc_info:
            ApiKeyUpdate(allowed_ips=["invalid.ip"])

        assert "Invalid IP address or CIDR notation" in str(exc_info.value)


class TestApiKeyModels:
    """Test complete API key models."""

    def test_api_key_model(self, sample_api_key_data):
        """Test complete ApiKey model."""
        api_key = ApiKey(**sample_api_key_data)

        assert api_key.id == sample_api_key_data["id"]
        assert api_key.key_hash == sample_api_key_data["key_hash"]
        assert api_key.name == sample_api_key_data["name"]
        assert api_key.is_active is True
        assert api_key.permissions_scope == ["read"]

    def test_api_key_response_excludes_sensitive_data(self, sample_api_key_data):
        """Test ApiKeyResponse excludes sensitive fields."""
        # Remove sensitive fields
        response_data = {
            k: v for k, v in sample_api_key_data.items() if k not in ["key_hash"]
        }

        response = ApiKeyResponse(**response_data)

        assert hasattr(response, "key_prefix")
        assert not hasattr(response, "key_hash")
        assert response.name == sample_api_key_data["name"]

    def test_api_key_with_plain_text(self, sample_api_key_data):
        """Test ApiKeyWithPlainText model."""
        response_data = {
            k: v for k, v in sample_api_key_data.items() if k not in ["key_hash"]
        }
        key_info = ApiKeyResponse(**response_data)

        with_plain = ApiKeyWithPlainText(
            api_key="sk_live_test123456789", key_info=key_info
        )

        assert with_plain.api_key == "sk_live_test123456789"
        assert with_plain.key_info.name == sample_api_key_data["name"]

    def test_api_key_stats(self):
        """Test ApiKeyStats model."""
        stats = ApiKeyStats(
            total_keys=10,
            active_keys=8,
            inactive_keys=2,
            total_requests=1000,
            requests_last_24h=100,
            most_active_key="sk_live_abcd",
        )

        assert stats.total_keys == 10
        assert stats.active_keys == 8
        assert stats.inactive_keys == 2
        assert stats.total_requests == 1000


class TestApiKeyGeneration:
    """Test API key generation utilities."""

    def test_generate_api_key_format(self):
        """Test API key generation format and length."""
        api_key, prefix = generate_api_key()

        # Test format
        assert api_key.startswith("sk_live_")
        assert len(api_key) == 64  # 8 + 56
        assert len(prefix) == 12  # sk_live_ + 4 chars

        # Test that it contains only alphanumeric characters
        random_part = api_key[8:]  # Remove "sk_live_"
        assert random_part.isalnum()

    def test_generate_api_key_uniqueness(self):
        """Test that generated keys are unique."""
        keys = [generate_api_key()[0] for _ in range(100)]
        assert len(set(keys)) == 100  # All unique

    def test_generate_api_key_prefix_consistency(self):
        """Test that prefix matches key start."""
        api_key, prefix = generate_api_key()
        assert api_key.startswith(prefix)


class TestApiKeyHashing:
    """Test API key hashing and verification."""

    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = "sk_live_test123456789"
        hashed = hash_api_key(api_key)

        # Should be bcrypt hash
        assert hashed.startswith("$2b$")
        assert len(hashed) >= 50  # bcrypt hashes are typically 60 chars

        # Different calls should produce different hashes (due to salt)
        hashed2 = hash_api_key(api_key)
        assert hashed != hashed2

    def test_verify_api_key_correct(self):
        """Test verifying correct API key."""
        api_key = "sk_live_test123456789"
        hashed = hash_api_key(api_key)

        assert verify_api_key(api_key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """Test verifying incorrect API key."""
        api_key = "sk_live_test123456789"
        wrong_key = "sk_live_wrong123456789"
        hashed = hash_api_key(api_key)

        assert verify_api_key(wrong_key, hashed) is False

    def test_verify_api_key_invalid_hash(self):
        """Test verifying with invalid hash."""
        api_key = "sk_live_test123456789"
        invalid_hash = "invalid_hash"

        assert verify_api_key(api_key, invalid_hash) is False

    @patch("bcrypt.checkpw")
    def test_verify_api_key_bcrypt_error(self, mock_checkpw):
        """Test handling bcrypt errors gracefully."""
        mock_checkpw.side_effect = ValueError("Bcrypt error")

        result = verify_api_key("test_key", "test_hash")
        assert result is False


class TestIpAllowlistChecking:
    """Test IP allowlist functionality."""

    def test_check_ip_allowed_no_restrictions(self):
        """Test that no restrictions allows all IPs."""
        assert check_ip_allowed("192.168.1.1", None) is True
        assert check_ip_allowed("10.0.0.1", []) is True

    def test_check_ip_allowed_exact_match(self):
        """Test exact IP address matching."""
        allowed_ips = ["192.168.1.100"]

        assert check_ip_allowed("192.168.1.100", allowed_ips) is True
        assert check_ip_allowed("192.168.1.101", allowed_ips) is False

    def test_check_ip_allowed_cidr_range(self):
        """Test CIDR range matching."""
        allowed_ips = ["192.168.1.0/24"]

        assert check_ip_allowed("192.168.1.1", allowed_ips) is True
        assert check_ip_allowed("192.168.1.100", allowed_ips) is True
        assert check_ip_allowed("192.168.1.255", allowed_ips) is True
        assert check_ip_allowed("192.168.2.1", allowed_ips) is False

    def test_check_ip_allowed_multiple_ranges(self):
        """Test multiple allowed IP ranges."""
        allowed_ips = ["192.168.1.0/24", "10.0.0.0/8", "203.0.113.42/32"]

        assert check_ip_allowed("192.168.1.50", allowed_ips) is True
        assert check_ip_allowed("10.5.10.20", allowed_ips) is True
        assert check_ip_allowed("203.0.113.42", allowed_ips) is True
        assert check_ip_allowed("172.16.0.1", allowed_ips) is False

    def test_check_ip_allowed_ipv6(self):
        """Test IPv6 address checking."""
        allowed_ips = ["::1", "2001:db8::/32"]

        assert check_ip_allowed("::1", allowed_ips) is True
        assert check_ip_allowed("2001:db8::1", allowed_ips) is True
        assert check_ip_allowed("2001:db9::1", allowed_ips) is False

    def test_check_ip_allowed_invalid_client_ip(self):
        """Test handling invalid client IP addresses."""
        allowed_ips = ["192.168.1.0/24"]

        assert check_ip_allowed("invalid.ip", allowed_ips) is False
        assert check_ip_allowed("", allowed_ips) is False
        assert check_ip_allowed(None, allowed_ips) is False

    def test_check_ip_allowed_invalid_allowed_ip(self):
        """Test handling invalid IPs in allowlist."""
        # This should be caught by validation, but test defensive behavior
        allowed_ips = ["invalid.range"]

        # Should return False for safety
        assert check_ip_allowed("192.168.1.1", allowed_ips) is False


@pytest.mark.unit
class TestApiKeyUtilities:
    """Unit tests for API key utility functions."""

    def test_integration_key_generation_and_verification(self):
        """Test full cycle: generate -> hash -> verify."""
        # Generate key
        api_key, prefix = generate_api_key()

        # Hash it
        hashed = hash_api_key(api_key)

        # Verify it
        assert verify_api_key(api_key, hashed) is True

        # Verify wrong key fails
        wrong_key, _ = generate_api_key()
        assert verify_api_key(wrong_key, hashed) is False

    def test_ip_allowlist_edge_cases(self):
        """Test edge cases for IP allowlist checking."""
        # Empty allowlist should allow all
        assert check_ip_allowed("1.2.3.4", []) is True

        # Single IP as /32
        allowed_ips = ["192.168.1.100/32"]
        assert check_ip_allowed("192.168.1.100", allowed_ips) is True
        assert check_ip_allowed("192.168.1.101", allowed_ips) is False

        # Localhost variations
        allowed_ips = ["127.0.0.1", "::1"]
        assert check_ip_allowed("127.0.0.1", allowed_ips) is True
        assert check_ip_allowed("::1", allowed_ips) is True
