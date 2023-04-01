from typing import List, Union, Callable
import subprocess
from pathlib import Path
import shutil
from .logger import logger
import stat
import os


def popen(cmd: List[str], output_prepend: str = "") -> Union[str, int]:
    """
    Run a command and yield the output line by line.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
    )
    for stdout_line in iter(proc.stdout.readline, ""):
        yield output_prepend + stdout_line
    proc.stdout.close()
    yield proc.stderr.read()
    proc.stderr.close()
    yield proc.wait()


def run(
    cmd: List[str], return_codes: Union[List[int], int] = 0, output_prepend: str = ""
) -> int:
    """
    Run a command and return the exit code.
    """
    logger().debug("executing command:", " ".join(cmd))

    return_code = 0

    for output in popen(cmd, output_prepend):
        if isinstance(output, str):
            logger().debug(output)
        else:
            return_code = output

    if isinstance(return_codes, int):
        return_codes = [return_codes]

    if return_code not in return_codes:
        logger().fatal_error(
            f'command failed! Command "{" ".join(cmd)}" returned unexpected exit code: {return_code}'
        )

    return return_code


# docker run --rm $volume_params -w "/layer" "$docker_image" /bin/bash -c "$install_command && $zip_command"
def docker_run(
    container: str, workdir: str, volume: str, container_cmd: Union[str, List[str]]
):
    """
    Run a command in a docker container.
    :param container: The docker container to run the command in.
    :param workdir: The working directory to run the command in.
    :param volume: The volume to mount into the container.
    :param container_cmd: The command to run in the container.
    """
    cmd = ["docker", "run", "--rm", "-v", volume, "-w", workdir, container]
    if isinstance(container_cmd, str):
        cmd.append(container_cmd)
    else:
        cmd.extend(container_cmd)

    return run(cmd, output_prepend="docker run>\t")


def docker_cp(image_hash: str, local_dir: str):
    """
    Copy a file or directory from a container to the host.
    :param image_hash: The hash of the image to copy from.
    :param local_dir: The local directory to copy to.
    """
    return run(
        ["docker", "cp", f"{image_hash}:/opt/layer.zip", local_dir],
        output_prepend="docker cp>\t",
    )


def docker_build(
    dockerfile: str = "Dockerfile", ctx_dir: str = ".", quiet: bool = True
):
    """
    Build a docker image.
    :param dockerfile: The path to the Dockerfile to build.
    :param ctx_dir: The context directory to build the Dockerfile in.
    :param quiet: Whether to suppress the build output.
    """
    cmd = ["docker", "build", "-f", dockerfile, ctx_dir]
    if quiet:
        cmd = cmd[0:2] + ["--quiet"] + cmd[2:]
    return run(cmd)


def docker_container_rm(container_hash: str):
    return run(
        [
            "docker",
            "container",
            "rm",
            container_hash,
        ]
    )


def docker_image_rm(image_hash: str):
    return run(
        [
            "docker",
            "image",
            "rm",
            image_hash,
        ]
    )


def path_copy(source: Path, target: Path):
    """
    Copy a file or directory to a target directory.
    :param source: The source file or directory to copy.
    :param target: The target directory to copy the source to.
    """
    if source.is_dir():
        with logger().status(f"copying contents of {source} into {target}..."):
            try:
                target.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target)
            except Exception as e:
                logger().fatal_error(
                    f"Failed copying {source} contents into {target}: {str(e)}"
                )
            logger().success(f"{source} contents were copied into {target}")
            return

    if source.is_file():
        with logger().status(f"copying {source} to {target}..."):
            try:
                if target.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                shutil.copy(source, target)
            except Exception as e:
                logger().fatal_error(f"Failed copying {source} to {target}: {str(e)}")
            logger().success(f"{source} was copied to {target}")
            return

    logger().fatal_error(f"{source} does not exist!")


def path_move(source: Path, target: Path):
    """
    Move a file or directory to a target directory.
    :param source: The source file or directory to move.
    :param target: The target directory to move the source to.
    """
    if source.is_dir():
        with logger().status(f"moving contents of {source} into {target}..."):
            try:
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy(source, target)
                rmtree(source)
            except Exception as e:
                logger().fatal_error(
                    f"Failed moving {source} contents " f"into {target}: {str(e)}"
                )
            logger().success(f"{source} contents were moved into {target}")
            return

    if source.is_file():
        with logger().status(f"moving {source} to {target}..."):
            try:
                target.mkdir(parents=True, exist_ok=True)
                logger().success(f"created directory {target}")
                shutil.move(source, target)
            except Exception as e:
                logger().fatal_error(f"Failed moving {source} to {target}: {str(e)}")
            logger().success(f"{source} was moved to {target}")
            return

    logger().fatal_error(f"{source} does not exist!")


def _rmtree_onerror(func: Callable, path: os.PathLike, exc_info):
    """
    Error handler for ``shutil.rmtree`` that attempts to fix access permissions errors

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    """

    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def rmtree(p: os.PathLike):
    """
    Remove a directory tree.
    """
    shutil.rmtree(p, onerror=_rmtree_onerror)
