import asyncio
import logging
from src.services.verb_service import VerbService

logger = logging.getLogger(__name__)

ETRE_VERBS = [
    "être",
    "naître",
    "mourir",
    "monter",
    "rester",
    "sortir",
    "venir",
    "aller",
    "arriver",
    "entrer",
    "rentrer",
    "tomber",
    "retourner",
    "descendre",
    "partir",
    "passer",
    "devenir",
    "revenir",
]

AVOIR_VERBS = [
    "avoir",
    "parler",
    "aimer",
    "regarder",
    "penser",
    "trouver",
    "donner",
    "demander",
    "manger",
    "chanter",
    "jouer",
    "travailler",
    "étudier",
    "finir",
    "choisir",
    "réussir",
    "vendre",
    "attendre",
    "entendre",
    "répondre",
    "perdre",
    "faire",
    "dire",
    "pouvoir",
    "vouloir",
    "savoir",
    "voir",
    "devoir",
    "croire",
    "prendre",
    "comprendre",
    "apprendre",
    "mettre",
    "permettre",
    "promettre",
    "boire",
    "lire",
    "écrire",
    "décrire",
    "vivre",
    "suivre",
    "rire",
    "sourire",
    "ouvrir",
    "découvrir",
    "offrir",
    "dormir",
    "sentir",
    "servir",
    "courir",
]

PRONOMINAL_VERBS = [
    "s'appeler",
    "se lever",
    "se laver",
    "se promener",
    "s'habiller",
    "s'arrêter",
    "se souvenir",
    "se coucher",
    "se sentir",
    "s'asseoir",
]

COI_TEST_VERBS = [
    "appartenir",
    "enseigner",
    "expliquer",
    "montrer",
    "obéir",
    "plaire",
    "réfléchir",
]


async def init_verbs():
    """Seeds the database with a predefined list of French verbs in parallel."""
    verb_service = VerbService()
    logger.info("Starting to seed verbs into the database...")

    all_verbs = ETRE_VERBS + AVOIR_VERBS + PRONOMINAL_VERBS + COI_TEST_VERBS

    tasks = []
    for infinitive in all_verbs:
        # Create a task for each verb download
        tasks.append(verb_service.download_verb(infinitive, target_language_code="eng"))

    logger.info(f"Queueing up {len(tasks)} verbs for parallel processing...")

    # Run all tasks concurrently and wait for them to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process the results
    for infinitive, result in zip(all_verbs, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to process verb '{infinitive}': {result}")
        else:
            logger.info(f"Successfully processed '{infinitive}'.")

    logger.info("Verb seeding process completed.")
