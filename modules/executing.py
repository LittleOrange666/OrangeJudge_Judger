import math
import os
import shutil
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass

import _judger

from modules import constants
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


def run(cmd: list[str], tl: int = 1000, ml: int = 128, in_file: str = "/dev/null", out_file: str = "/dev/null",
        err_file: str = "/dev/null", seccomp_rule_name: str | None = None,
        uid: int = constants.nobody_uid, reverse_io: int = 0) -> Result:
    # tl: ms ml: MB
    exe_path = cmd[0]
    if not exe_path.startswith("/"):
        which_exe_path = shutil.which(exe_path)
        if which_exe_path is not None:
            exe_path = which_exe_path
    log_file = temp_filename()
    ret = _judger.run(max_cpu_time=tl,
                      max_real_time=tl + 1000,
                      max_memory=ml * 1024 * 1024,
                      max_process_number=200,
                      max_output_size=128 * 1024 * 1024,
                      max_stack=math.ceil(ml / 4) * 1024 * 1024,
                      # five args above can be _judger.UNLIMITED
                      exe_path=exe_path,
                      input_path=in_file,
                      output_path=out_file,
                      error_path=err_file,
                      # can be empty list
                      args=cmd[1:],
                      # can be empty list
                      env=["PATH=/usr/bin"],
                      log_path=log_file,
                      # can be None
                      seccomp_rule_name=seccomp_rule_name,
                      uid=uid,
                      gid=uid,
                      reverse_io=reverse_io)
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


def interact_run(cmd: list[str], interact_cmd: list[str], tl: int = 1000, ml: int = 128, in_file: str = "/dev/null",
                 out_file: str = "/dev/null",
                 err_file: str = "/dev/null", interact_err_file: str = "/dev/null",
                 seccomp_rule_name: str | None = None, interact_seccomp_rule_name: str | None = None,
                 uid: int = constants.nobody_uid, interact_uid: int = constants.nobody_uid):
    fifo1 = temp_filename()
    fifo2 = temp_filename()
    os.mkfifo(fifo1)
    os.mkfifo(fifo2)
    inter_res: Result | None = None

    def run_inter():
        nonlocal inter_res
        inter_res = run(interact_cmd + [in_file, out_file], tl, ml, fifo1, fifo2, interact_err_file,
                        interact_seccomp_rule_name, interact_uid, 1)

    t = threading.Thread(target=run_inter)
    t.start()
    res = run(cmd, tl, ml, fifo2, fifo1, err_file, seccomp_rule_name, uid)
    t.join()
    return InteractResult(result=res, interact_result=inter_res)


def call(cmd: list[str], user: User | None = None, stdin: str = "", timeout: float | None = None) -> tuple[
    str, str, int]:
    if user is not None:
        cmd = ["sudo", "-u", user.value] + cmd
    print(*cmd)
    if timeout is None:
        timeout = 30
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        ret = process.communicate(stdin.encode("utf8"), timeout=timeout)
        return ret[0].decode("utf8"), ret[1].decode("utf8"), process.returncode
    except subprocess.TimeoutExpired:
        process.kill()
        return "TLE", "TLE", 777777
