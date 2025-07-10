from cli.sentences.features import IndirectPronounFeature
from pathlib import Path
from schemas.sentence import IndirectPronoun

import pytest
import sys

# Add the parent directory to the path for imports
parent_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(parent_dir))


@pytest.mark.skip(reason="Not implemented yet")
def test_explicit_indirect_pronoun():
    indirect_pronoun_feature: IndirectPronounFeature = IndirectPronounFeature(
        feature=IndirectPronoun.feminine
    )

    prompt: str = indirect_pronoun_feature.prompt()

    assert indirect_pronoun_feature.feature is IndirectPronoun.feminine
    assert IndirectPronoun.feminine.prompt in prompt


def test_explicit_incorrect_indirect_pronoun():
    indirect_pronoun_feature: IndirectPronounFeature = IndirectPronounFeature(
        feature=IndirectPronoun.feminine, incorrect=True
    )

    prompt: str = indirect_pronoun_feature.prompt()

    assert indirect_pronoun_feature.feature is not IndirectPronoun.feminine
    assert IndirectPronoun.feminine.prompt not in prompt


def test_random_correct_indirect_pronoun():
    indirect_pronoun_feature: IndirectPronounFeature = IndirectPronounFeature(
        is_random=True
    )
    assert indirect_pronoun_feature.feature is not IndirectPronoun.NONE


def test_no_indirect_pronoun():
    indirect_pronoun_feature: IndirectPronounFeature = IndirectPronounFeature(
        feature=IndirectPronoun.NONE
    )
    assert indirect_pronoun_feature.feature is IndirectPronoun.NONE
