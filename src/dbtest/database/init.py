from ..verbs.get import fetch_verb

auxiliaries: list[str] = ["avoir", "être"]
irregulars: list[str] = ["aller", "faire", "pouvoir", "savoir", "vouloir"]

async def init_auxiliaries():
    [await fetch_verb(verb, True) for verb in auxiliaries]
