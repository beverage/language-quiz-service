from dataclasses import dataclass

from dbtest.sentances.models import DirectObject, IndirectPronoun, Negation, Sentence

import logging
import random

@dataclass
class SentenceFeatures:

    #   TODO: add error-forcing flags once prompts are more reliable for all of these and the auxiliary once the prompts are more reliable:

    direct_object:      bool = False
    indirect_pronoun:   bool = False
    reflexive:          bool = False    #   Not used yet - all verbs are explicitly reflexive or not.
    negated:            bool = False
    
    def randomize(self, sentence: Sentence) -> Sentence:

        sentence.direct_object    = random.choice([p for p in DirectObject if p is not DirectObject.none])
        sentence.indirect_pronoun = random.choice([p for p in IndirectPronoun if p is not IndirectPronoun.none and p.name is not sentence.direct_object.name])
        sentence.negation         = random.choice([n for n in Negation])

        logging.debug(sentence.direct_object)
        logging.debug(sentence.indirect_pronoun)
        logging.debug(sentence.negation)

        return sentence
