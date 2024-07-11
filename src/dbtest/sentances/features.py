from dataclasses import dataclass

from dbtest.database.metadata import Base
from dbtest.database.sentences import DirectObject

import logging
import random

@dataclass
class SentenceFeatures:

    #   TODO: add error-forcing flags once prompts are more reliable for all of these and the auxiliary once the prompts are more reliable:

    direct_pronoun:     bool = False
    indirect_pronoun:   bool = False    #   Not used yet.
    reflexive:          bool = False    #   Not used yet - all verbs are explicitly reflexive or not.
    negated:            bool = False    #   Not used yet.
    
    def randomize(self, sentence):

        sentence.direct_pronoun = (
            random.choice([p for p in DirectObject if p is not DirectObject.none]))# if self.direct_pronoun else DirectPronoun.none))

        logging.debug(sentence.direct_pronoun)

        return sentence
