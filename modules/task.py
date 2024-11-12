from modules import executing, tools
from dataclasses import asdict


def run(filename: str, lang_name: str, in_file: str):
    lang = executing.langs[lang_name]
    env = executing.Environment()
    file = env.send_file(filename)
    compile_result = lang.compile(file, env)
    ret = {"compile": compile_result}
    ce = len(compile_result[1])
    if ce:
        return ret
    exec_cmd = lang.get_execmd(compile_result[0])
    out_file = "tmp/out.txt"
    result = executing.run(exec_cmd, in_file=in_file, out_file=out_file, seccomp_rule_name=lang.seccomp_rule_name)
    ret["out"] = tools.read(out_file)
    ret["result"] = asdict(result)
    return ret
