from typing import List, Union
import subprocess
from pathlib import Path
import shutil
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
        logger().fatal_error(f'command failed! Command "{" ".join(cmd)}" returned unexpected exit code: {return_code}')

    return return_code


def path_copy(source: Path, target: Path):
    if source.is_dir():
        with logger().status(f'copying contents of {source} into {target}...'):
            try:
                if not target.is_dir():
                    target.mkdir()
                    logger().success(f'created directory {target}')
                shutil.copytree(source, target)
            except Exception as e:
                logger().fatal_error(f'Failed copying {source} contents '
                                     f'into {target}: {str(e)}')
            logger().success(f'{source} contents were copied into {target}')
            return

    if source.is_file():
        with logger().status(f'copying {source} to {target}...'):
            try:
                if not target.is_dir():
                    target.mkdir()
                    logger().success(f'created directory {target}')
                shutil.copy(source, target)
            except Exception as e:
                logger().fatal_error(f'Failed copying {source} to {target}: {str(e)}')
            logger().success(f'{source} was copied to {target}')
            return

    logger().fatal_error(f'{source} does not exist!')


def path_move(source: Path, target: Path):
    if source.is_dir():
        with logger().status(f'moving contents of {source} into {target}...'):
            try:
                if not target.is_dir():
                    target.mkdir()
                    logger().success(f'created directory {target}')
                shutil.copy(source, target)
                shutil.rmtree(source)
            except Exception as e:
                logger().fatal_error(f'Failed moving {source} contents '
                                     f'into {target}: {str(e)}')
            logger().success(f'{source} contents were moved into {target}')
            return

    if source.is_file():
        with logger().status(f'moving {source} to {target}...'):
            try:
                if not target.is_dir():
                    target.mkdir()
                    logger().success(f'created directory {target}')
                shutil.move(source, target)
            except Exception as e:
                logger().fatal_error(f'Failed moving {source} to {target}: {str(e)}')
            logger().success(f'{source} was moved to {target}')
            return

    logger().fatal_error(f'{source} does not exist!')