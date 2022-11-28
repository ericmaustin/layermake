import logging
from typing import List, Union
import subprocess
from .ctx import ctx


def popen(cmd: List[str]) -> Union[str, int]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(proc.stdout.readline, ""):
        yield stdout_line
    proc.stdout.close()
    yield proc.stderr.read()
    proc.stderr.close()
    yield proc.wait()


def run(cmd: List[str], return_codes: Union[List[int], int] = 0) -> int:
    ctx().debug('executing command:', ' '.join(cmd))

    return_code = 0

    for output in popen(cmd):
        if isinstance(output, str):
            ctx().debug(output)
        else:
            return_code = output

    if isinstance(return_codes, int):
        return_codes = [return_codes]

    if return_code not in return_codes:
        ctx().fatal_error(f'{" ".join(cmd)} returned unexpected exit code: {return_code}')

    return return_code

