from enum import Enum

from modules import judger

root_uid = 0
judge_uid = 1500
compile_uid = 1600
runner_uid = 1700
nobody_uid = 65534

judegr_result: dict[int, str] = {judger.RESULT_SUCCESS: "AC",
                                 judger.RESULT_WRONG_ANSWER: "WA",
                                 judger.RESULT_CPU_TIME_LIMIT_EXCEEDED: "TLE",
                                 judger.RESULT_REAL_TIME_LIMIT_EXCEEDED: "TLE",
                                 judger.RESULT_MEMORY_LIMIT_EXCEEDED: "MLE",
                                 judger.RESULT_RUNTIME_ERROR: "RE",
                                 judger.RESULT_SYSTEM_ERROR: "JE"}
judger_error: dict[int, str] = {judger.ERROR_INVALID_CONFIG: "ERROR_INVALID_CONFIG",
                                judger.ERROR_FORK_FAILED: "ERROR_FORK_FAILED",
                                judger.ERROR_PTHREAD_FAILED: "ERROR_PTHREAD_FAILED",
                                judger.ERROR_WAIT_FAILED: "ERROR_WAIT_FAILED",
                                judger.ERROR_ROOT_REQUIRED: "ERROR_ROOT_REQUIRED",
                                judger.ERROR_LOAD_SECCOMP_FAILED: "ERROR_LOAD_SECCOMP_FAILED",
                                judger.ERROR_SETRLIMIT_FAILED: "ERROR_SETRLIMIT_FAILED",
                                judger.ERROR_DUP2_FAILED: "ERROR_DUP2_FAILED",
                                judger.ERROR_SETUID_FAILED: "ERROR_SETUID_FAILED",
                                judger.ERROR_EXECVE_FAILED: "ERROR_EXECVE_FAILED",
                                judger.ERROR_SPJ_ERROR: "ERROR_SPJ_ERROR"}


class SeccompRule(str, Enum):
    c_cpp = "c_cpp"
    c_cpp_file_io = "c_cpp_file_io"
    general = "general"
    golang = "golang"
    node = "node"


class User(str, Enum):
    root = "root"
    judge = "judge"
    compile = "compile"
    running = "running"
    nobody = "nobody"


class InitOp(str, Enum):
    init = "init"
    check = "check"
