from typing import List, Union
import subprocess
from .logger import logger


def popen(cmd: List[str]) -> Union[str, int]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(proc.stdout.readline, ""):
        yield stdout_line
    proc.stdout.close()
    yield proc.stderr.read()
    proc.stderr.close()
    yield proc.wait()


def run(cmd: List[str], return_codes: Union[List[int], int] = 0) -> int:
    logger().debug('executing command:', ' '.join(cmd))

    return_code = 0

    for output in popen(cmd):
        if isinstance(output, str):
            logger().debug(output)
        else:
            return_code = output

    if isinstance(return_codes, int):
        return_codes = [return_codes]

    if return_code not in return_codes:
        logger().fatal_error(f'{" ".join(cmd)} returned unexpected exit code: {return_code}')

    return return_code

