from enum import Enum

import _judger

root_uid = 0
judge_uid = 1500
compile_uid = 1600
runner_uid = 1600
nobody_uid = 65534

judegr_result: dict[int, str] = {_judger.RESULT_SUCCESS: "AC",
                                 _judger.RESULT_WRONG_ANSWER: "WA",
                                 _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED: "TLE",
                                 _judger.RESULT_REAL_TIME_LIMIT_EXCEEDED: "TLE",
                                 _judger.RESULT_MEMORY_LIMIT_EXCEEDED: "MLE",
                                 _judger.RESULT_RUNTIME_ERROR: "RE",
                                 _judger.RESULT_SYSTEM_ERROR: "JE"}
judger_error: dict[int, str] = {_judger.ERROR_INVALID_CONFIG: "ERROR_INVALID_CONFIG",
                                _judger.ERROR_FORK_FAILED: "ERROR_FORK_FAILED",
                                _judger.ERROR_PTHREAD_FAILED: "ERROR_PTHREAD_FAILED",
                                _judger.ERROR_WAIT_FAILED: "ERROR_WAIT_FAILED",
                                _judger.ERROR_ROOT_REQUIRED: "ERROR_ROOT_REQUIRED",
                                _judger.ERROR_LOAD_SECCOMP_FAILED: "ERROR_LOAD_SECCOMP_FAILED",
                                _judger.ERROR_SETRLIMIT_FAILED: "ERROR_SETRLIMIT_FAILED",
                                _judger.ERROR_DUP2_FAILED: "ERROR_DUP2_FAILED",
                                _judger.ERROR_SETUID_FAILED: "ERROR_SETUID_FAILED",
                                _judger.ERROR_EXECVE_FAILED: "ERROR_EXECVE_FAILED",
                                _judger.ERROR_SPJ_ERROR: "ERROR_SPJ_ERROR"}


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
    nobody = "nobody"
