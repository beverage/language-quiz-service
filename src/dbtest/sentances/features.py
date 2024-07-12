from dataclasses import dataclass

from dbtest.database.sentences import DirectObject, IndirectPronoun

import logging
import random

@dataclass
class SentenceFeatures:

    #   TODO: add error-forcing flags once prompts are more reliable for all of these and the auxiliary once the prompts are more reliable:

    direct_object:      bool = False
    indirect_object:    bool = False    #   Dative pronouns only.
    reflexive:          bool = False    #   Not used yet - all verbs are explicitly reflexive or not.
    negated:            bool = False    #   Not used yet.
    
    def randomize(self, sentence):

        sentence.direct_object = (
            random.choice([p for p in DirectObject if p is not DirectObject.none]))

        sentence.indirect_object = (
            random.choice([p for p in IndirectPronoun if p is not IndirectPronoun.none and p.name is not sentence.direct_object.name]))

        logging.debug(sentence.direct_object)
        logging.debug(sentence.indirect_object)

        return sentence
