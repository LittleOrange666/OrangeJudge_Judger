import asyncio
import math
import os
import shutil
import sys
import uuid
from dataclasses import dataclass

from modules import constants
from modules import judger
from modules.constants import User


def random_string() -> str:
    return uuid.uuid4().hex


def temp_filename():
    return "/tmp/" + random_string()


@dataclass
class Result:
    cpu_time: int  # ms
    real_time: int  # ms
    memory: int  # Bytes
    signal: int
    exit_code: int
    error: str
    result: str
    error_id: int
    result_id: int
    judger_log: int = ""


@dataclass
class InteractResult:
    result: Result
    interact_result: Result


async def calls(cmds: list[list[str]], cwd: str | None = None):
    for cmd in cmds:
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=cwd)
        await proc.wait()


async def run(cmd: list[str], tl: int = 1000, ml: int = 128, in_file: str = "/dev/null", out_file: str = "/dev/null",
              err_file: str = "/dev/null", seccomp_rule_name: str | None = None,
              uid: int = constants.nobody_uid, reverse_io: int = 0, cwd: str | None = None) -> Result:
    # tl: ms ml: MB
    exe_path = cmd[0]
    if not exe_path.startswith("/"):
        which_exe_path = shutil.which(exe_path)
        if which_exe_path is not None:
            exe_path = which_exe_path
    log_file = temp_filename()
    old_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)
    ret = await judger.run(max_cpu_time=tl,
                           max_real_time=tl + 1000,
                           max_memory=ml * 1024 * 1024,
                           max_process_number=200,
                           max_output_size=128 * 1024 * 1024,
                           max_stack=math.ceil(ml / 4) * 1024 * 1024,
                           exe_path=exe_path,
                           input_path=in_file,
                           output_path=out_file,
                           error_path=err_file,
                           args=cmd[1:],
                           env=["PATH=/usr/bin"],
                           log_path=log_file,
                           seccomp_rule_name=seccomp_rule_name,
                           uid=uid,
                           gid=uid,
                           reverse_io=reverse_io)
    os.chdir(old_cwd)
    ret["result_id"] = ret["result"]
    ret["error_id"] = ret["error"]
    ret["result"] = constants.judegr_result.get(ret["result"], "unknown")
    ret["error"] = constants.judger_error.get(ret["error"], "UNKNOWN_ERROR") if ret["error"] else "NO_ERROR"
    print(exe_path, cmd[1:], file=sys.stderr)
    if os.path.exists(log_file):
        with open(log_file) as f:
            ret["judger_log"] = f.read()
        os.remove(log_file)
    return Result(**ret)


async def interact_run(cmd: list[str], interact_cmd: list[str], tl: int = 1000, ml: int = 128,
                       in_file: str = "/dev/null",
                       out_file: str = "/dev/null",
                       err_file: str = "/dev/null", interact_err_file: str = "/dev/null",
                       seccomp_rule_name: str | None = None, interact_seccomp_rule_name: str | None = None,
                       uid: int = constants.nobody_uid, interact_uid: int = constants.nobody_uid,
                       cwd: str | None = None):
    fifo1 = temp_filename()
    fifo2 = temp_filename()
    os.mkfifo(fifo1)
    os.mkfifo(fifo2)
    old_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)
    inter_res_wait = run(interact_cmd + [in_file, out_file], tl, ml, fifo1, fifo2, interact_err_file,
                         interact_seccomp_rule_name, interact_uid, 1)
    res_wait = run(cmd, tl, ml, fifo2, fifo1, err_file, seccomp_rule_name, uid)
    inter_res = await inter_res_wait
    res = await res_wait
    os.chdir(old_cwd)
    return InteractResult(result=res, interact_result=inter_res)


async def call(cmd: list[str], user: User | None = None, stdin: str = "", timeout: float | None = None,
               cwd: str | None = None) -> tuple[str, str, int]:
    if user is not None:
        cmd = ["sudo", "-u", user.value] + cmd
    print(*cmd)
    if timeout is None:
        timeout = 30
    process = await asyncio.create_subprocess_exec(*cmd, stdin=asyncio.subprocess.PIPE,
                                                   stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                                                   cwd=cwd)
    try:
        ret = await asyncio.wait_for(process.communicate(stdin.encode("utf8")), timeout)
        return ret[0].decode("utf8"), ret[1].decode("utf8"), process.returncode
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return "TLE", "TLE", 777777
