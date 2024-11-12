from fastapi import FastAPI, Body, File, UploadFile
import uvicorn
import asyncio
from pydantic import BaseModel

from modules import executing, task

app = FastAPI()


@app.post("/test")
async def test():
    await asyncio.sleep(100)
    return {"result": "ok"}


@app.post("/run")
async def run(lang: str = Body(...), file: UploadFile = File(...), in_file: UploadFile = File(...)):
    with open(f"tmp/{file.filename}", "wb") as f:
        f.write(file.file.read())
    file.file.close()
    with open(f"tmp/{in_file.filename}", "wb") as f:
        f.write(in_file.file.read())
    in_file.file.close()
    res = task.run(f"tmp/{file.filename}", lang, f"tmp/{in_file.filename}")
    return res

if __name__ == '__main__':
    executing.init()
    uvicorn.run(app, host='0.0.0.0', port=8000)
