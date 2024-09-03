from fastapi import FastAPI

from ..sentences.create import create_sentence

app = FastAPI()

@app.get("/hello")
async def hello():
    return "Hello, world!"

@app.get("/sentence")
async def sentence():
    return await create_sentence("savoir")
