from lqconsole.sentences.features import IndirectPronounFeature
from lqconsole.sentences.models import IndirectPronoun

def test_explicit_direct_object():

    direct_object_feature: IndirectPronounFeature=IndirectPronounFeature(feature=IndirectPronoun.feminine)

    prompt: str=direct_object_feature.prompt()

    assert direct_object_feature.feature is IndirectPronoun.feminine
    assert IndirectPronoun.feminine.prompt in prompt

def test_explicit_incorrect_direct_object():

    direct_object_feature: IndirectPronounFeature=IndirectPronounFeature(
        feature=IndirectPronoun.feminine,
        incorrect=True)

    prompt: str=direct_object_feature.prompt()

    assert direct_object_feature.feature is not IndirectPronoun.feminine
    assert IndirectPronoun.feminine.prompt not in prompt

def test_random_correct_direct_object():

    direct_object_feature: IndirectPronounFeature=IndirectPronounFeature(is_random=True)
    assert direct_object_feature.feature is not IndirectPronoun.none

def test_no_direct_object():
    direct_object_feature: IndirectPronounFeature=IndirectPronounFeature(feature=IndirectPronoun.none)
    assert direct_object_feature.feature is IndirectPronoun.none
