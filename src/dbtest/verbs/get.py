from ..models.conjugation import Conjugation

import json
import logging

from openai import OpenAI

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

log = logging.getLogger(__name__)

client:    OpenAI = OpenAI()
openai_model: str = "gpt-3.5-turbo"
openai_role:  str = "user"

engine  = create_engine("postgresql://postgres:postgres@localhost/language_app")
Session = sessionmaker(bind = engine)
session = Session()

auxiliaries: list[str] = [ "avoir", "être"]

def generate_verb_prompt(verb: str):
    return f"""Give me the present, passé composé (as passe_compose), imparfait, future tense, \
            and past participle (as participle) of the French verb {verb}, \
            with english translations, with each verb mode being a json object of the format: \
            verb tense (as 'tense'): {{   \
                infinitive: {verb} \
                conjugations: [ \
                    {{  \
                        french pronoun (as 'pronoun'): \
                        conjugated verb, without its pronoun (as 'verb'):    \
                        english translation (as 'translation'): \
                    }}  \
                ]   \
            }} \
            Do not return any newlines in the response. \
            Always use both genders in the 3rd person pronouns.  \
            Always include 'on' for the 3rd person singular form.  \
            Replace spaces with _ in the tense names. \
            Remove all accent marks on the pronouns. \
            The first person pronoun should always be 'je' instead of j' or j. \
            The pronouns should always be "-" for participles. \
            All json property names and values need to be enclosed in double quotes. \
            """

def fetch_verb(verb: str, save: bool) -> str:

    completion = client.chat.completions.create(
        model    = openai_model,
        messages = [
            { "role": openai_role, "content": generate_verb_prompt(verb) }
        ]
    )

    if save:

        response = completion.choices[0].message.content
        reponse_json = json.loads(response)

        for tense in reponse_json:

            response_tense = reponse_json[tense]
            infinitive = response_tense["infinitive"]

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
            else:
                log.info(f"Updating {conjugation.infinitive} with tense {conjugation.tense}.")
                session.merge(conjugation)

            session.commit()

    return completion.choices[0].message.content

def fetch_auxiliaries() -> tuple[str, str]:
    pass
