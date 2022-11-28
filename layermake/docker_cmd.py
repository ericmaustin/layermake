from typing import List, Union
from . import proc


# docker run --rm $volume_params -w "/layer" "$docker_image" /bin/bash -c "$install_command && $zip_command"
def run(container: str, workdir: str, volume: str, container_cmd: Union[str, List[str]]):
    cmd = [
        'docker',
        'run',
        '--rm',
        '-v', volume,
        '-w', workdir,
        container
    ]
    if isinstance(container_cmd, str):
        cmd.append(container_cmd)
    else:
        cmd.extend(container_cmd)

    return proc.run(cmd)


def cp(image_hash: str, local_dir: str):
    return proc.run([
        'docker',
        'cp',
        f'{image_hash}:/opt/layer.zip',
        local_dir
    ])


def build(dockerfile: str = 'Dockerfile', ctx_dir: str = '.', quiet: bool = True):
    cmd = [
        'docker',
        'build',
        '-f', dockerfile,
        ctx_dir
    ]
    if quiet:
        cmd = cmd[0:2] + ['--quiet'] + cmd[2:]
    return proc.run(cmd)


def container_rm(container_hash: str):
    return proc.run([
        'docker',
        'container',
        'rm',
        container_hash,
    ])


def image_rm(image_hash: str):
    return proc.run([
        'docker',
        'image',
        'rm',
        image_hash,
    ])

