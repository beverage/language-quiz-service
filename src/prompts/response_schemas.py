"""OpenAI JSON schemas for structured LLM responses."""

from typing import Any


def get_correct_sentence_response_schema() -> dict[str, Any]:
    """Returns OpenAI JSON schema for correct sentence generation.

    Correct sentences require translation but no explanation.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "correct_sentence_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "sentence": {
                        "type": "string",
                        "description": "The French sentence without error",
                    },
                    "translation": {
                        "type": "string",
                        "description": "English translation of the sentence",
                    },
                    "negation": {
                        "type": "string",
                        "description": "The negation type used in the sentence",
                        "enum": [
                            "none",
                            "pas",
                            "jamais",
                            "rien",
                            "personne",
                            "plus",
                            "aucun",
                            "aucune",
                        ],
                    },
                    "direct_object": {
                        "type": "string",
                        "description": "Grammatical gender/number of direct object pronoun",
                        "enum": ["none", "masculine", "feminine", "plural"],
                    },
                    "indirect_object": {
                        "type": "string",
                        "description": "Grammatical gender/number of indirect object pronoun",
                        "enum": ["none", "masculine", "feminine", "plural"],
                    },
                    "has_compliment_object_direct": {
                        "type": "boolean",
                        "description": "True if COD pronoun (le/la/les) is used before verb",
                    },
                    "has_compliment_object_indirect": {
                        "type": "boolean",
                        "description": "True if COI pronoun (lui/leur) is used before verb",
                    },
                },
                "required": [
                    "sentence",
                    "translation",
                    "negation",
                    "direct_object",
                    "indirect_object",
                    "has_compliment_object_direct",
                    "has_compliment_object_indirect",
                ],
                "additionalProperties": False,
            },
        },
    }


def get_incorrect_sentence_response_schema() -> dict[str, Any]:
    """Returns OpenAI JSON schema for incorrect sentence generation.

    Incorrect sentences require explanation but no translation.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "incorrect_sentence_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "sentence": {
                        "type": "string",
                        "description": "The French sentence with deliberate grammatical error",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Explanation of the grammatical error",
                    },
                    "negation": {
                        "type": "string",
                        "description": "The negation type used in the sentence",
                        "enum": [
                            "none",
                            "pas",
                            "jamais",
                            "rien",
                            "personne",
                            "plus",
                            "aucun",
                            "aucune",
                        ],
                    },
                    "direct_object": {
                        "type": "string",
                        "description": "Grammatical gender/number of direct object pronoun",
                        "enum": ["none", "masculine", "feminine", "plural"],
                    },
                    "indirect_object": {
                        "type": "string",
                        "description": "Grammatical gender/number of indirect object pronoun",
                        "enum": ["none", "masculine", "feminine", "plural"],
                    },
                    "has_compliment_object_direct": {
                        "type": "boolean",
                        "description": "True if COD pronoun (le/la/les) is used before verb",
                    },
                    "has_compliment_object_indirect": {
                        "type": "boolean",
                        "description": "True if COI pronoun (lui/leur) is used before verb",
                    },
                },
                "required": [
                    "sentence",
                    "explanation",
                    "negation",
                    "direct_object",
                    "indirect_object",
                    "has_compliment_object_direct",
                    "has_compliment_object_indirect",
                ],
                "additionalProperties": False,
            },
        },
    }
