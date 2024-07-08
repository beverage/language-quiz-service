from dbtest.database.metadata import Base

from dbtest.ai.client import AsyncChatGPTClient
from dbtest.database.conjugations import Tense
from dbtest.database.metadata import metadata
from dbtest.database.sentences import Pronoun

from dbtest.sentances.prompts import SentencePromptGenerator
from dbtest.verbs.get import download_verb, get_verb, get_random_verb

import random

def select_verb():

    Conjugation = Base.classes.conjugations
    Verb = Base.classes.verbs
    pass

def create_sentence(verb: str):
    
    Conjugation = Base.classes.conjugations
    Verb = Base.classes.verbs
    pass

async def create_random_sentence(openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    Conjugation = Base.classes.conjugations
    Verb = Base.classes.verbs
    Sentence = Base.classes.sentences

    verb: Verb = await get_random_verb()

    sentence: Sentence = Sentence()
    sentence.infinitive = verb.infinitive
    sentence.auxiliary = verb.auxiliary
    sentence.pronoun = random.choice([p for p in Pronoun])

    # This raises the question as to if we even need participles if we are just
    # going to feed the tense right into ChatGTP:
    sentence.tense = random.choice([t for t in Tense if t is not Tense.participle])

    sentence.is_correct = True
    
    generator: SentencePromptGenerator = SentencePromptGenerator()
    prompt: str = generator.generate_sentence_prompt(sentence)
    print(prompt)
    
#     response: str = await openapi_client.handle_request(prompt=generate_verb_prompt(verb_infinitive=requested_verb))
#     response_json = json.loads(response)
#     infinitive: str = response_json["infinitive"]

    response: str = await openapi_client.handle_request(prompt=prompt)
    print(response)
    
    return sentence