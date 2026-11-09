import asyncio
import math
import os
import pwd
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass

from modules import constants
from modules import judger
from modules.constants import User


# extra address space (MB) granted on top of 2 * ml when only the RSS is checked
MEMORY_CHECK_ONLY_EXTRA_AS = 4096


def random_string() -> str:
    return uuid.uuid4().hex


def temp_filename():
    return "/tmp/" + random_string()


def primary_gid(uid: int) -> int:
    """
    The primary group of ``uid``. ``useradd --system`` gives the sandbox users groups whose gid differs from
    their uid (e.g. judge = 1500:999), and OrangeJudge grants access with ``chgrp <user>``, so processes must
    run with the user's real group instead of gid = uid.
    """
    try:
        return pwd.getpwuid(uid).pw_gid
    except KeyError:
        return uid


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


@dataclass
class CommunicateResult:
    results: list[Result]
    interact_result: Result


async def calls(cmds: list[list[str]], cwd: str | None = None):
    for cmd in cmds:
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=cwd)
        await proc.wait()


async def run(cmd: list[str], tl: int = 1000, ml: int = 128, in_file: str = "/dev/null", out_file: str = "/dev/null",
              err_file: str = "/dev/null", seccomp_rule_name: str | None = None,
              uid: int = constants.nobody_uid, reverse_io: int = 0, cwd: str | None = None,
              memory_limit_check_only: bool = False) -> Result:
    # tl: ms ml: MB
    # memory_limit_check_only: do not limit the address space to 2 * ml, only compare the peak RSS against ml.
    # Needed by runtimes that reserve a lot of virtual memory up front (Go ~700MB, Node.js ~1.3GB, JVM).
    # The address space is still capped generously so a runaway program cannot exhaust the host's memory.
    address_space_limit = (ml * 2 + MEMORY_CHECK_ONLY_EXTRA_AS) * 1024 * 1024 if memory_limit_check_only else None
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
                           gid=primary_gid(uid),
                           reverse_io=reverse_io,
                           memory_limit_check_only=int(memory_limit_check_only),
                           address_space_limit=address_space_limit)
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
                       cwd: str | None = None, memory_limit_check_only: bool = False):
    fifo1 = temp_filename()
    fifo2 = temp_filename()
    os.mkfifo(fifo1)
    os.mkfifo(fifo2)
    old_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)
    inter_res_wait = run(interact_cmd + [in_file, out_file], tl, ml, fifo1, fifo2, interact_err_file,
                         interact_seccomp_rule_name, interact_uid, 1)
    res_wait = run(cmd, tl, ml, fifo2, fifo1, err_file, seccomp_rule_name, uid,
                   memory_limit_check_only=memory_limit_check_only)
    try:
        # both processes must run concurrently, otherwise opening the fifos blocks forever
        inter_res, res = await asyncio.gather(inter_res_wait, res_wait)
    finally:
        os.chdir(old_cwd)
        for fifo in (fifo1, fifo2):
            if os.path.exists(fifo):
                os.remove(fifo)
    return InteractResult(result=res, interact_result=inter_res)


async def communicate_run(cmd: list[str], interact_cmd: list[str], num_processes: int = 1, tl: int = 1000,
                          ml: int = 128, in_file: str = "/dev/null", out_file: str = "/dev/null",
                          err_file: str = "/dev/null", interact_err_file: str = "/dev/null",
                          seccomp_rule_name: str | None = None, interact_seccomp_rule_name: str | None = None,
                          uid: int = constants.nobody_uid, interact_uid: int = constants.nobody_uid,
                          interact_tl: int | None = None, cwd: str | None = None,
                          memory_limit_check_only: bool = False) -> CommunicateResult:
    """
    CMS "Communication" style judging with N user processes.

    For every process i two FIFOs are created: ``from_i`` (user -> manager) and ``to_i`` (manager -> user).
    The manager is executed as ``interact_cmd in_file out_file from_0 to_0 from_1 to_1 ...`` with stdin/stdout
    bound to /dev/null; it has to open each pair in the order from_i then to_i.
    User process i is executed as ``cmd i`` with stdin = to_i and stdout = from_i.
    """
    if num_processes < 1:
        raise ValueError("num_processes must be positive")
    fifo_dir = tempfile.mkdtemp(prefix="communicate_")
    try:
        # only the manager (interact_uid) may access the fifos by name; user processes get them as stdio,
        # which libjudger opens before dropping privileges.
        os.chown(fifo_dir, interact_uid, primary_gid(interact_uid))
        os.chmod(fifo_dir, 0o700)
        pairs: list[tuple[str, str]] = []
        for i in range(num_processes):
            fifo_from = os.path.join(fifo_dir, f"from_{i}")
            fifo_to = os.path.join(fifo_dir, f"to_{i}")
            for fifo in (fifo_from, fifo_to):
                os.mkfifo(fifo, 0o600)
                os.chown(fifo, interact_uid, primary_gid(interact_uid))
            pairs.append((fifo_from, fifo_to))
        old_cwd = os.getcwd()
        if cwd is not None:
            os.chdir(cwd)
        try:
            manager_args = interact_cmd + [in_file, out_file] + [f for pair in pairs for f in pair]
            manager_wait = run(manager_args, tl if interact_tl is None else interact_tl, ml, "/dev/null",
                               "/dev/null", interact_err_file, interact_seccomp_rule_name, interact_uid)
            # reverse_io=1: open stdout (from_i) first, matching the manager's from_i -> to_i open order
            user_waits = [run(cmd + [str(i)], tl, ml, fifo_to, fifo_from, err_file, seccomp_rule_name, uid, 1,
                              memory_limit_check_only=memory_limit_check_only)
                          for i, (fifo_from, fifo_to) in enumerate(pairs)]
            all_res = await asyncio.gather(manager_wait, *user_waits)
        finally:
            os.chdir(old_cwd)
        return CommunicateResult(results=list(all_res[1:]), interact_result=all_res[0])
    finally:
        shutil.rmtree(fifo_dir, ignore_errors=True)


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
