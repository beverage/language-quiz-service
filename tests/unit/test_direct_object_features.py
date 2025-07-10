from cli.sentences.features import DirectObjectFeature
from pathlib import Path
from schemas.sentence import DirectObject

import pytest
import sys

# Add the parent directory to the path for imports
parent_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(parent_dir))


@pytest.mark.skip(reason="Not implemented yet")
def test_explicit_direct_object():
    direct_object_feature: DirectObjectFeature = DirectObjectFeature(
        feature=DirectObject.feminine
    )

    prompt: str = direct_object_feature.prompt()

    assert direct_object_feature.feature is DirectObject.feminine
    assert DirectObject.feminine.prompt in prompt


def test_explicit_incorrect_direct_object():
    direct_object_feature: DirectObjectFeature = DirectObjectFeature(
        feature=DirectObject.feminine, incorrect=True
    )

    prompt: str = direct_object_feature.prompt()

    assert direct_object_feature.feature is not DirectObject.feminine
    assert DirectObject.feminine.prompt not in prompt


def test_random_correct_direct_object():
    direct_object_feature: DirectObjectFeature = DirectObjectFeature(is_random=True)
    assert direct_object_feature.feature is not DirectObject.NONE


def test_no_direct_object():
    direct_object_feature: DirectObjectFeature = DirectObjectFeature(
        feature=DirectObject.NONE
    )
    assert direct_object_feature.feature is DirectObject.NONE
