"""Tests for OpenAI client error categorization."""

import pytest

from src.clients.openai_client import OpenAIClient


class TestOpenAIErrorCategorization:
    """Test the _categorize_error method for proper error classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = OpenAIClient()

    def test_categorize_insufficient_funds_quota_exceeded(self):
        """Test detection of insufficient funds error (quota exceeded)."""
        error = Exception("You exceeded your current quota, please check your plan")

        result = self.client._categorize_error(error)

        assert result == "insufficient_funds"

    def test_categorize_insufficient_funds_insufficient_quota(self):
        """Test detection of insufficient funds error (insufficient quota)."""
        error = Exception("Insufficient quota available")

        result = self.client._categorize_error(error)

        assert result == "insufficient_funds"

    def test_categorize_timeout_error_message(self):
        """Test detection of timeout from error message."""
        error = Exception("Connection timeout after 30 seconds")

        result = self.client._categorize_error(error)

        assert result == "timeout"

    def test_categorize_rate_limit_message(self):
        """Test detection of rate limit from error message."""
        error = Exception("Rate limit reached for requests")

        result = self.client._categorize_error(error)

        assert result == "rate_limit"

    def test_categorize_unknown_error(self):
        """Test handling of unknown error types."""
        error = ValueError("Something unexpected happened")

        result = self.client._categorize_error(error)

        assert result == "unknown"

    def test_categorize_error_case_insensitive(self):
        """Test that error detection is case-insensitive."""
        error = Exception("INSUFFICIENT QUOTA EXCEEDED")

        result = self.client._categorize_error(error)

        assert result == "insufficient_funds"
