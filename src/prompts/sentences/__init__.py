"""Sentence prompt generation system.

This module provides a compositional system for generating French sentence prompts
with targeted error injection for grammar exercises.

Usage:
    from src.prompts.sentences import SentencePromptBuilder, ErrorType

    builder = SentencePromptBuilder()
    prompt = builder.build_prompt(sentence, verb, conjugations, error_type=ErrorType.WRONG_CONJUGATION)
"""

from src.prompts.sentences.builder import SentencePromptBuilder
from src.prompts.sentences.error_types import ErrorType

__all__ = ["SentencePromptBuilder", "ErrorType"]
