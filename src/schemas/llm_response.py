"""Data classes for LLM response metadata.

These classes capture the full response from LLM calls, including
reasoning traces for gpt-5 models, enabling debugging and analysis.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Rich response from LLM including all metadata for observability.

    This captures everything needed to debug, analyze, and reproduce
    a generation, including the reasoning trace from gpt-5 models.

    Attributes:
        content: The actual response content (cleaned of markdown)
        model: Model identifier used for generation
        response_id: OpenAI response ID for correlation
        duration_ms: Request duration in milliseconds
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        total_tokens: Total tokens (prompt + completion)
        reasoning_tokens: Reasoning tokens used (gpt-5 models only)
        reasoning_content: The reasoning trace text (gpt-5 models only)
        raw_content: Uncleaned response content
    """

    content: str
    model: str
    response_id: str
    duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    reasoning_tokens: int | None = None
    reasoning_content: str | None = None
    raw_content: str | None = None

    def to_trace_dict(
        self, prompt_text: str | None = None, prompt_version: str = "1.0"
    ) -> dict[str, Any]:
        """Convert to dictionary format for storage in generation_trace.

        Args:
            prompt_text: The full prompt that was sent (optional but recommended)
            prompt_version: Version tag for the prompt template

        Returns:
            Dictionary suitable for JSONB storage
        """
        trace = {
            "model": self.model,
            "prompt_version": prompt_version,
            "response_id": self.response_id,
            "generation_time_ms": round(self.duration_ms, 2),
            # Token usage
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            # Quality tracking (defaults, to be updated by caller)
            "quality_status": "approved",
            "quality_issues": [],
        }

        # Add reasoning-specific fields if present
        if self.reasoning_tokens is not None:
            trace["reasoning_tokens"] = self.reasoning_tokens

        if self.reasoning_content is not None:
            trace["reasoning_content"] = self.reasoning_content

        # Add prompt if provided
        if prompt_text is not None:
            trace["prompt_text"] = prompt_text

        return trace


@dataclass
class SentenceGenerationTrace:
    """Trace data for a single sentence generation within a problem.

    Problems consist of multiple sentences, each with their own generation.
    This captures per-sentence metadata while the problem-level trace
    aggregates the overall generation.
    """

    sentence_index: int
    is_correct: bool
    error_type: str | None  # e.g., "wrong_conjugation", "wrong_auxiliary"
    llm_response: LLMResponse
    prompt_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for inclusion in problem trace."""
        return {
            "sentence_index": self.sentence_index,
            "is_correct": self.is_correct,
            "error_type": self.error_type,
            "model": self.llm_response.model,
            "response_id": self.llm_response.response_id,
            "generation_time_ms": round(self.llm_response.duration_ms, 2),
            "prompt_tokens": self.llm_response.prompt_tokens,
            "completion_tokens": self.llm_response.completion_tokens,
            "total_tokens": self.llm_response.total_tokens,
            "reasoning_tokens": self.llm_response.reasoning_tokens,
            "reasoning_content": self.llm_response.reasoning_content,
            "prompt_text": self.prompt_text,
        }


@dataclass
class ProblemGenerationTrace:
    """Complete trace for a problem generation, aggregating sentence traces.

    This is the top-level structure stored in problems.generation_trace.
    """

    model: str
    prompt_version: str
    total_generation_time_ms: float
    sentence_traces: list[SentenceGenerationTrace] = field(default_factory=list)
    quality_status: str = "approved"
    quality_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSONB storage."""
        # Aggregate token usage across all sentences
        total_prompt_tokens = sum(
            s.llm_response.prompt_tokens for s in self.sentence_traces
        )
        total_completion_tokens = sum(
            s.llm_response.completion_tokens for s in self.sentence_traces
        )
        total_reasoning_tokens = sum(
            s.llm_response.reasoning_tokens or 0 for s in self.sentence_traces
        )

        return {
            "model": self.model,
            "prompt_version": self.prompt_version,
            "total_generation_time_ms": round(self.total_generation_time_ms, 2),
            # Aggregated token usage
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_reasoning_tokens": total_reasoning_tokens
            if total_reasoning_tokens > 0
            else None,
            # Per-sentence breakdown
            "sentences": [s.to_dict() for s in self.sentence_traces],
            # Quality tracking
            "quality_status": self.quality_status,
            "quality_issues": self.quality_issues,
        }

    def add_sentence_trace(self, trace: SentenceGenerationTrace) -> None:
        """Add a sentence generation trace."""
        self.sentence_traces.append(trace)

    @property
    def sentence_count(self) -> int:
        """Number of sentences generated."""
        return len(self.sentence_traces)
