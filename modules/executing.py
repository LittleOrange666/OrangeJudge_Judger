import os
import sys
import shutil
from typing import Callable
from dataclasses import dataclass

import _judger

from modules import tools, constants


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


def run(cmd: list[str], tl: int = 1000, ml: int = 128, in_file: str = "/dev/null", out_file: str = "/dev/null",
        err_file: str = "/dev/null", seccomp_rule_name: str | None = None,
        uid: int = constants.nobody_uid) -> Result:
    # tl: ms ml: MB
    exe_path = cmd[0]
    if not exe_path.startswith("/"):
        exe_path = shutil.which(exe_path)
    ret = _judger.run(max_cpu_time=tl,
                      max_real_time=tl + 1000,
                      max_memory=ml * 1024 * 1024,
                      max_process_number=200,
                      max_output_size=128 * 1024 * 1024,
                      max_stack=ml // 4 * 1024 * 1024,
                      # five args above can be _judger.UNLIMITED
                      exe_path=exe_path,
                      input_path=in_file,
                      output_path=out_file,
                      error_path=err_file,
                      # can be empty list
                      args=cmd[1:],
                      # can be empty list
                      env=["PATH=/usr/bin"],
                      log_path="tmp/judger.log",
                      # can be None
                      seccomp_rule_name=seccomp_rule_name,
                      uid=uid,
                      gid=uid)
    ret["result_id"] = ret["result"]
    ret["error_id"] = ret["error"]
    ret["result"] = constants.judegr_result.get(ret["result"], "unknown")
    ret["error"] = constants.judger_error.get(ret["error"], "UNKNOWN_ERROR") if ret["error"] else "NO_ERROR"
    print(exe_path, cmd[1:], file=sys.stderr)
    if os.path.exists("tmp/judger.log"):
        ret["judger_log"] = tools.read("tmp/judger.log")
        os.remove("tmp/judger.log")
    return Result(**ret)


def is_tle(result: tuple[str, str, int]) -> bool:
    return result == ("TLE", "TLE", 777777)


class Environment:
    __slots__ = ("path", "dirname")

    def __init__(self):
        self.dirname: str = tools.random_string()
        self.path = os.path.abspath(os.path.join("runtimes", self.dirname))
        os.makedirs(self.path)

    def send_file(self, filepath: str, nxt: Callable[[str], None] | None = None) -> str:
        # tools.log("send", filepath)
        file_abspath = os.path.abspath(filepath)
        shutil.copy(file_abspath, self.path)
        if nxt is None:
            self.protected(filepath)
        else:
            nxt(filepath)
        return self.filepath(file_abspath)

    def get_file(self, filepath: str, source: None | str = None) -> None:
        file_abspath = os.path.abspath(filepath)
        if source is None:
            source = os.path.basename(filepath)
        if self.dirname not in source:
            source = os.path.join(self.dirname, source)
        shutil.move(os.path.join(os.path.abspath("runtimes"), source), os.path.dirname(file_abspath))

    def simple_path(self, filepath: str) -> str:
        target = os.path.basename(filepath)
        if os.path.join(f"/{self.dirname}", filepath) != f"/{self.dirname}/{target}":
            shutil.move(os.path.join(self.path, filepath), os.path.join(self.path, target))
        return target

    def rm_file(self, filepath: str) -> None:
        os.remove(self.filepath(filepath))

    def filepath(self, filename: str) -> str:
        if filename.startswith(self.path):
            return filename
        return self.path + "/" + (
            filename if filename.count("/") <= 2 and "__pycache__" in filename else os.path.basename(filename))

    def fullfilepath(self, filename: str) -> str:
        return self.filepath(filename)

    def exist(self, filename: str) -> bool:
        return os.path.exists(self.fullfilepath(filename))

    def judge_writeable(self, *filenames: str) -> None:
        for filename in filenames:
            if not self.exist(filename):
                tools.create(self.fullfilepath(filename))
            filepath = self.filepath(filename)
            os.chown(filepath, constants.root_uid, constants.judge_uid)
            os.chmod(filepath, 0o760)

    def writeable(self, *filenames: str) -> None:
        for filename in filenames:
            if not self.exist(filename):
                tools.create(self.fullfilepath(filename))
            filepath = self.filepath(filename)
            os.chmod(filepath, 0o766)

    def judge_executable(self, *filenames: str) -> None:
        for filename in filenames:
            filepath = self.filepath(filename)
            os.chown(filepath, constants.root_uid, constants.judge_uid)
            os.chmod(filepath, 0o750)

    def executable(self, *filenames: str) -> None:
        for filename in filenames:
            filepath = self.filepath(filename)
            os.chmod(filepath, 0o755)

    def readable(self, *filenames: str) -> None:
        for filename in filenames:
            filepath = self.filepath(filename)
            os.chmod(filepath, 0o744)

    def judge_readable(self, *filenames: str) -> None:
        for filename in filenames:
            filepath = self.filepath(filename)
            os.chown(filepath, constants.root_uid, constants.judge_uid)
            os.chmod(filepath, 0o740)

    def protected(self, *filenames: str) -> None:
        for filename in filenames:
            filepath = self.filepath(filename)
            os.chmod(filepath, 0o700)

    def __del__(self):
        pass
        # shutil.rmtree(self.path)


class Language:
    def __init__(self, name: str, branch: str | None = None):
        self.name = name
        self.data = tools.read_json(f"langs/{name}.json")
        self.branch = self.data["default_branch"] if branch is None else branch
        self.kwargs = self.data["branches"][self.branch]
        self.seccomp_rule_name = self.data["seccomp_rule_name"]

    def compile(self, filename: str, env: Environment) -> tuple[str, str]:
        if self.data["require_compile"]:
            new_filename = os.path.splitext(filename)[0]
            dirname = os.path.dirname(new_filename)
            new_filename = env.filepath(self.data["exec_name"].format(os.path.basename(new_filename), **self.kwargs))
            compile_cmd = self.data["compile_cmd"][:]
            for i in range(len(compile_cmd)):
                compile_cmd[i] = compile_cmd[i].format(filename, new_filename, **self.kwargs)
            out_file = env.filepath("compile.log")
            out = run(compile_cmd, out_file=out_file, err_file=out_file,
                      uid=constants.compile_uid)
            if out.exit_code:
                # tools.log(out[1])
                return new_filename, tools.read(out_file)
            new_filename = env.simple_path(new_filename)
            env.executable(new_filename)
            new_filename = os.path.join(dirname, new_filename)
            return new_filename, ""
        env.executable(filename)
        return filename, ""

    def get_execmd(self, filename: str) -> list[str]:
        exec_cmd = self.data["exec_cmd"][:]
        for i in range(len(exec_cmd)):
            exec_cmd[i] = exec_cmd[i].format(filename,
                                             os.path.basename(os.path.splitext(filename)[0]),
                                             folder=os.path.dirname(filename), **self.kwargs)
        return exec_cmd


langs: dict[str, Language] = {}


def init():
    for lang in os.listdir("langs"):
        lang_name = os.path.splitext(lang)[0]
        dat = tools.read_json(f"langs/{lang_name}.json")
        keys = dat["branches"].keys()
        for key in keys:
            langs[key] = Language(lang_name, key)
