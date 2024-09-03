from dataclasses import dataclass

import logging
import random

from dbtest.ai.promptable import Promptable
from dbtest.sentences.models import DirectObject, IndirectPronoun, Negation, Sentence
from dbtest.utils.prompt_enum import PromptEnum

from abc import ABC

# How do we enforce the existence of a 'none' on our prompt enums?  We can do that in Python,
# but will it mess with sqlalchemy?  That needs to be tested, otherwise this can break easily.
class SentenceFeature(Promptable, ABC):

    def __init__(self, feature: PromptEnum, incorrect: bool=False, is_random: bool=False):

        self.feature   = feature
        self.incorrect = incorrect
        self.is_random = is_random

        if incorrect:
            self.feature = random.choice([f for f in self.__feature() if f is not self.feature.none and f.name is not self.feature.name])
        elif is_random:
            self.feature = random.choice([f for f in self.__feature() if f is not self.feature.none])

    def __feature(self):
        return self.feature.__class__

class DirectObjectFeature(SentenceFeature):
    def __init__(self, feature: PromptEnum=DirectObject.none, incorrect: bool=False, is_random: bool=False):
        super().__init__(feature, incorrect, is_random)

    def prompt(self) -> str:
        if self.random:
            return "The sentence may or may not have a direct object before its verb."
        elif self.incorrect is False:
            return f"The sentence must have a correct {self.feature.prompt} direct object before its verb."
        else:
            return f"The sentence must have an incorrect {self.feature.prompt} direct object before its verb."

class IndirectPronounFeature(SentenceFeature):
    def __init__(self, feature: PromptEnum=IndirectPronoun.none, incorrect: bool=False, is_random: bool=False):
        super().__init__(feature, incorrect, is_random)

    def prompt(self) -> str:
        if self.random:
            return "The sentence may or may not have an indirect pronoun before its verb."
        elif self.incorrect is False:
            return f"The sentence must have a correct {self.feature.prompt} indirect pronoun as a pronoun before its verb."
        else:
            return f"The sentence must have an incorrect {self.feature.prompt} indirect pronoun as a pronoun before its verb."

class NegationFeature(SentenceFeature):
    def __init__(self, feature: PromptEnum=Negation.none, incorrect: bool=False, is_random: bool=False):
        super().__init__(feature, incorrect, is_random)

    def prompt(self) -> str:
        if self.random:
            return "The sentence may or may not be negated, in any way."
        elif self.feature is not self.feature.none:
            return f"The sentence must contain the negation {self.feature.prompt}."
        else:
            return "The sentence must not contain any negations."

@dataclass
class SentenceFeatures():
    pass

@dataclass
class SentenceFeaturesOld():

    direct_object:      bool = False
    indirect_pronoun:   bool = False
    reflexive:          bool = False    #   Not used yet - all verbs are explicitly reflexive or not.
    negated:            bool = False

    def randomize(self, sentence: Sentence) -> Sentence:

        sentence.direct_object    = random.choice([p for p in DirectObject if p is not DirectObject.none])
        sentence.indirect_pronoun = random.choice([p for p in IndirectPronoun if p is not IndirectPronoun.none and p.name is not sentence.direct_object.name])
        sentence.negation         = random.choice(list(Negation))

        logging.debug(sentence.direct_object)
        logging.debug(sentence.indirect_pronoun)
        logging.debug(sentence.negation)

        return sentence
