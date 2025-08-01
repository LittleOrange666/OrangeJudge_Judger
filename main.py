import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from pydantic import BaseModel

from modules import executing, constants
from modules.executing import InteractResult, Result
from modules.constants import SeccompRule, User, InitOp

app = FastAPI()

app.token = "<UNSET>" if "JUDGE_SERVER_TOKEN" not in os.environ else os.environ["JUDGE_SERVER_TOKEN"]

port = int(os.environ.get("JUDGE_SERVER_PORT", 8000))


def check_token(token: str):
    if token != app.token:
        print("user token=", token)
        print("expected token=", app.token)
        raise HTTPException(403)


class CallRequest(BaseModel):
    cmd: list[str]
    user: User | None = None
    stdin: str = ""
    timeout: float | None = None
    cwd: str | None = None
    cmds: list[list[str]] | None = None


@app.post("/call")
async def call(item: CallRequest, token: str = Header(...)):
    print(item.model_dump())
    check_token(token)
    if item.cmds is not None:
        await executing.calls(item.cmds, item.cwd)
    res = await executing.call(**item.model_dump(exclude={"cmds"}))
    return res


class JudgeRequest(BaseModel):
    cmd: list[str]
    tl: int = 1000
    ml: int = 128
    in_file: str = "/dev/null"
    out_file: str = "/dev/null"
    err_file: str = "/dev/null"
    seccomp_rule_name: SeccompRule | None = None
    uid: int = constants.nobody_uid
    cwd: str | None = None
    cmds: list[list[str]] | None = None


@app.post("/judge")
async def judge(item: JudgeRequest, token: str = Header(...)) -> Result:
    print(item.model_dump())
    check_token(token)
    if item.cmds is not None:
        await executing.calls(item.cmds, item.cwd)
    res = await executing.run(**item.model_dump(exclude={"cmds"}))
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
    seccomp_rule_name: SeccompRule | None = None
    interact_seccomp_rule_name: SeccompRule | None = None
    uid: int = constants.nobody_uid
    interact_uid: int = constants.nobody_uid
    cwd: str | None = None
    cmds: list[list[str]] | None = None


@app.post("/interact_judge")
async def interact_judge(item: InteractJudgeRequest, token: str = Header(...)) -> InteractResult:
    print(item.model_dump())
    check_token(token)
    if item.cmds is not None:
        await executing.calls(item.cmds, item.cwd)
    res = await executing.interact_run(**item.model_dump(exclude={"cmds"}))
    return res


class InitRequest(BaseModel):
    op: InitOp
    token: str


@app.post("/init")
async def init(item: InitRequest) -> str:
    print(item.model_dump())
    if item.op == InitOp.init:
        if app.token == "<UNSET>":
            app.token = item.token
            return "OK"
        else:
            return "TOKEN IS SET"
    else:
        if app.token == item.token:
            return "OK"
        else:
            return "FAILED"


@app.get("/health_check")
async def health_check():
    return JSONResponse(content={"status": "ok"})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=port)
