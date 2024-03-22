from ..database.conjugations import Conjugation
from ..database.verbs import Verb, Reflexivity

import json
import logging

from fix_busted_json import repair_json

from openai import OpenAI, ChatCompletion

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

log = logging.getLogger(__name__)

client:    OpenAI = OpenAI()
openai_model: str = "gpt-3.5-turbo"
openai_role:  str = "user"

engine  = create_engine("postgresql://postgres:postgres@localhost/language_app")
Session = sessionmaker(bind = engine)
session = Session()

auxiliaries: list[str] = [ "avoir", "être" ]

def generate_tense_list_prompt(verb_infinitive: str) -> str:
    return ""

def generate_reflexivity_prompt(verb_infinitive: str) -> str: 
    return """If the verb can only be used reflexively then return 'mandatory', \
              if the verb can be used both reflexive and non-reflexively return \
              'conditional', otherwise return 'no'."""

def generate_verb_tense_format(verb: str) -> str:
    return """ \
                {   \
                    verb tense (as tense): \
                    conjugations: [ \
                        {  \
                            french pronoun (as 'pronoun'): \
                            conjugated verb, without its pronoun (as 'verb'):    \
                            english translation (as 'translation'): \
                        }  \
                    ]   \
                } \
"""

def generate_extra_rules(verb_infinitive: str) -> str:
    return """Do not return any newlines in the response. \
            Always use both genders in the 3rd person pronouns.  \
            Always include 'on' for the 3rd person singular form.  \
            Replace spaces with _ in the tense names. \
            Remove all accent marks on the tense names. \
            The first person pronoun should always be 'je' instead of j' or j. \
            The pronouns should always be "-" for participles. \
            All json property names and values need to be enclosed in double quotes. \
            """

def generate_verb_prompt(verb_infinitive: str):
    #   This prompt still often returns mal-formed JSON, and accent marks where they are not wanted.
    #   Some manual response cleansing is required:
    return f"""Give me the present, passé composé (as passe_compose), imparfait, future simple tense, \
            and past participle (as participle), and auxiliary verb of the French verb {verb_infinitive}, \
            with english translations, with each verb mode being a json object of the format: \
                auxiliary: \
                infinitive: {verb_infinitive} \
                reflexivity: {generate_reflexivity_prompt(verb_infinitive)} \
                verb tense (as 'tenses'): [ \
                    {generate_verb_tense_format(verb_infinitive)} \
                ] \
            {generate_extra_rules(verb_infinitive)}
            """

def fetch_verb(requested_verb: str, save_verb: bool) -> str:

    completion: ChatCompletion = client.chat.completions.create(
        model    = openai_model,
        messages = [
            { "role": openai_role, "content": generate_verb_prompt(requested_verb) },
        ]
    )

    # print(completion.choices[0].message.content)

    if save_verb:

        response: str = repair_json(completion.choices[0].message.content) # JSON can often come back mal-formed by ChatGTP.
        response_json: str = json.loads(response)

        infinitive: str = response_json["infinitive"]

        for response_tense in response_json["tenses"]:

            tense = response_tense["tense"]

            existing_verb: Verb = (
                session.query(Verb)
                       .filter(Verb.infinitive == requested_verb)
                       .order_by(Verb.id.desc())
                       .first())

            if existing_verb != None:
                log.info(f"The verb {infinitive} already exists and will be updated if needed.")

            verb: Verb = Verb() if existing_verb == None else existing_verb
            verb.auxiliary   = response_json["auxiliary"]
            verb.infinitive  = infinitive
            verb.reflexivity = Reflexivity[response_json["reflexivity"]]

            existing_conjugation: Conjugation = (
                session.query(Conjugation)
                       .filter(and_(Conjugation.infinitive == infinitive, Conjugation.tense == tense))
                       .order_by(Conjugation.id.desc())
                       .first())

            if existing_conjugation != None:
                log.info(f"A verb conjugation for {infinitive}, {tense} already exists and will be updated.")

            conjugation: Conjugation = Conjugation() if existing_conjugation == None else existing_conjugation
            conjugation.infinitive   = infinitive
            conjugation.tense        = tense

            for response_conjugation in response_tense["conjugations"]:

                #   Should only set if response is not null to account for ChatGTP non-determinism:
                match response_conjugation["pronoun"]:
                    case "je" | "j'" | "j":
                        conjugation.first_person_singular = response_conjugation["verb"]
                    case "tu":
                        conjugation.second_person_singular = response_conjugation["verb"]
                    case "il/elle/on" | "il" | "elle" | "on":
                        conjugation.third_person_singular = response_conjugation["verb"]
                    case "nous":
                        conjugation.first_person_plural = response_conjugation["verb"]
                    case "vous":
                        conjugation.second_person_formal = response_conjugation["verb"]
                    case "ils/elles" | "ils" | "elles":
                        conjugation.third_person_plural = response_conjugation["verb"]
                    case "-":
                        conjugation.first_person_singular  = response_conjugation["verb"]
                        conjugation.second_person_singular = response_conjugation["verb"]
                        conjugation.third_person_singular  = response_conjugation["verb"]
                        conjugation.first_person_plural    = response_conjugation["verb"]
                        conjugation.second_person_formal   = response_conjugation["verb"]
                        conjugation.third_person_plural    = response_conjugation["verb"]
            
            if existing_conjugation == None:
                log.info(f"Adding {conjugation.infinitive} with tense {conjugation.tense}.")
                session.add(conjugation)
                session.add(verb)
            else:
                log.info(f"Updating {conjugation.infinitive} with tense {conjugation.tense}.")
                session.merge(conjugation)
                session.merge(verb)

            session.commit()

    return completion.choices[0].message.content
