import json
import logging

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from lqconsole.ai.client import AsyncChatGPTClient
from lqconsole.database.engine import get_async_session
from lqconsole.verbs.models import Verb, Conjugation
from lqconsole.verbs.prompts import generate_verb_prompt

async def get_verb(requested_verb: str, database_session: AsyncSession=get_async_session()) -> Verb:

    async with database_session as session:

        verb: Verb = (
        await session.scalars(select(Verb)
            .filter(Verb.infinitive == requested_verb)
            .order_by(Verb.id.desc()))).first()

        return verb

async def get_random_verb(database_session: AsyncSession=get_async_session()) -> Verb:
    # pylint: disable=not-callable
    async with database_session as session:

        verb: Verb = (
        await session.scalars(select(Verb)
            .order_by(func.random()))).first()

        return verb

async def download_verb(requested_verb: str, openapi_client: AsyncChatGPTClient=AsyncChatGPTClient()):

    logging.info("Fetching verb %s.", requested_verb)

    async with get_async_session() as session:

        logging.info("Saving verb %s", requested_verb)

        response: str = await openapi_client.handle_request(prompt=generate_verb_prompt(verb_infinitive=requested_verb))
        response_json = json.loads(response)
        infinitive: str = response_json["infinitive"]

        existing_verb: Verb = await get_verb(requested_verb=requested_verb, database_session=session)

        if existing_verb:
            logging.info("The verb %s already exists and will be updated if needed.", infinitive)
        else:
            logging.info("The verb %s does not yet exist in the database.", infinitive)

        verb: Verb = Verb() if existing_verb is None else existing_verb
        verb.auxiliary   = response_json["auxiliary"]
        verb.infinitive  = infinitive

        session.add(verb)
        await session.commit()

        for response_tense in response_json["tenses"]:

            tense = response_tense["tense"]

            existing_conjugation: Conjugation = (
                await session.scalars(select(Conjugation)
                    .filter(and_(Conjugation.infinitive == infinitive, Conjugation.tense == tense))
                    .order_by(Conjugation.id.desc()))).first()

            if existing_conjugation:
                logging.info("A verb conjugation for %s, %s already exists and will be updated.", infinitive, tense)
            else:
                logging.info("Verb conjugations are missing or are incomplete for %s and will be added/updated.", infinitive)

            conjugation: Conjugation = Conjugation() if existing_conjugation is None else existing_conjugation
            conjugation.infinitive   = infinitive
            conjugation.tense        = tense
            conjugation.verb_id      = verb.id

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

            #   Since we are using Postgres we can upsert instead of doing this:
            if existing_conjugation is None:
                logging.info("Adding %s with tense %s.", conjugation.infinitive, conjugation.tense)
                await session.merge(conjugation)
            else:
                logging.info("Updating %s with tense %s.", conjugation.infinitive, conjugation.tense)
                await session.merge(conjugation)

        return verb
