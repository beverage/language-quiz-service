from fastapi import FastAPI, HTTPException

from src.cli.sentences.create import create_sentence
from src.cli.webserver.verbs.get import get_verb_and_conjugations

app = FastAPI()


@app.get("/hello")
async def hello():
    return "Hello, world!"


@app.get("/sentence")
async def sentence():
    return await create_sentence("savoir")


@app.get("/verbs/{infinitive}")
async def get_verb(infinitive: str):
    data = await get_verb_and_conjugations(infinitive)
    if data is None:
        raise HTTPException(status_code=404, detail="Verb not found")
    return data
