import json
import os
import time
import uuid
from datetime import datetime


def create(*filename: str) -> None:
    with open(os.path.join(*filename), "w"):
        pass


def remove(*filename: str) -> None:
    try:
        os.remove(os.path.join(*filename))
    except FileNotFoundError:
        pass


def read_json(*filename: str) -> dict:
    with open(os.path.join(*filename)) as f:
        return json.load(f)


def read(*filename: str) -> str:
    with open(os.path.join(*filename)) as f:
        return f.read()


def exists(*filename: str) -> bool:
    return os.path.exists(os.path.join(*filename))


def elapsed(*filename: str) -> float:
    ret = time.time() - os.path.getmtime(os.path.join(*filename))
    if ret < 0:
        return 100
    return ret


def get_timestring() -> str:
    t = datetime.now()
    return f"{t.year}-{t.month}-{t.day} {t.hour}:{t.minute:0>2d}:{t.second:0>2d}"


def random_string() -> str:
    return uuid.uuid4().hex


def init():
    pass
