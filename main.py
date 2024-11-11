from fastapi import FastAPI
import uvicorn

from pydantic import BaseModel

from modules import executing, constants

app = FastAPI()


class CallRequest(BaseModel):
    cmd: list[str]


@app.post("/call")
async def call(item: CallRequest):
    res = executing.call(item.cmd)
    return res


class JudgeRequest(BaseModel):
    cmd: list[str]
    tl: int = 1000
    ml: int = 128
    in_file: str = "/dev/null"
    out_file: str = "/dev/null"
    err_file: str = "/dev/null"
    seccomp_rule_name: str | None = None
    uid: int = constants.nobody_uid


@app.post("/judge")
async def judge(item: JudgeRequest) -> JudgeRequest:
    res = executing.run(**item.dict())
    return res


class InteractJudgeRequest(BaseModel):
    cmd: list[str]
    interact_cmd: list[str]
    tl: int = 1000
    ml: int = 128
    in_file: str = "/dev/null"
    out_file: str = "/dev/null"
    err_file: str = "/dev/null"
    interact_err_file: str = "/dev/null"
    seccomp_rule_name: str | None = None
    uid: int = constants.nobody_uid
    interact_uid: int = constants.nobody_uid


@app.post("/interact_judge")
async def interact_judge(item: JudgeRequest) -> InteractJudgeRequest:
    res = executing.interact_run(**item.dict())
    return res


if __name__ == '__main__':
    executing.init()
    uvicorn.run(app, host='0.0.0.0', port=8000)
