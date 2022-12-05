from typing import List
from pathlib import Path
import click
from .python import PythonBundler
from .binary import BinaryBundler
from .node import NodeBundler
import boto3
from .publisher import LayerPublisher, click_common

client = boto3.client('lambda')

NODEJS_RUNTIMES = ['4.3', '6.10', '8.10', '10.x', '12.x', '14.x', '16.x']
PYTHON_RUNTIMES = ['3.6', '3.7', '3.8', '3.9']
BINARY_RUNTIMES = [
    'nodejs', 'nodejs4.3', 'nodejs6.10', 'nodejs8.10',
    'nodejs10.x', 'nodejs12.x', 'nodejs14.x', 'nodejs16.x',
    'java8', 'java8.al2', 'java11', 'python2.7',
    'python3.6', 'python3.7', 'python3.8', 'python3.9',
    'dotnetcore1.0', 'dotnetcore2.0', 'dotnetcore2.1', 'dotnetcore3.1',
    'dotnet6', 'nodejs4.3-edge', 'go1.x', 'ruby2.5',
    'ruby2.7', 'provided', 'provided.al2', 'nodejs18.x'
]


@click.group()
def cli():
    pass


@cli.command()
@click_common
@click.option('-r', '--runtime',
              help='nodejs runtime')
@click.option('-m', '--manifest',
              help='nodejs manifest file (package.json)')
@click.option('-o', '--output',
              default=str(Path('./layer')),
              help='target output directory',
              show_default=True)
@click.option('--container',
              type=str,
              help='use the provided docker container to build the layer')
@click.option('--dir',
              help='directory containing artifacts to bundle into a layer')
@click.argument('packages', nargs=-1)
def nodejs(
        publisher: LayerPublisher,
        runtime: str,
        manifest,
        output,
        container,
        dir,
        packages
):

    while not runtime:
        runtime = input(f'NodeJS runtime ({",".join(NODEJS_RUNTIMES)}): ').strip()
        if runtime not in NODEJS_RUNTIMES:
            print(f'runtime must be one of ({",".join(NODEJS_RUNTIMES)})!')

    if not manifest and not packages and not dir:
        packages = input('NodeJS Packages:').strip()

    runtime = runtime.replace('nodejs', '')
    if '.' not in runtime:
        runtime = runtime + '.x'
    _runtime_name = f'nodejs{runtime}'

    publisher.runtimes = [_runtime_name]
    bundler = NodeBundler(runtime=runtime,
                          artifact_dir=dir,
                          local_dir=output,
                          container=container,
                          manifest=manifest,
                          packages=packages)
    publisher.publish_layer(bundler.bundle(), _runtime_name)


@cli.command()
@click_common
@click.option('-r', '--runtime',
              help='python runtime')
@click.option('-m', '--manifest',
              help='python manifest file (requirements.txt)')
@click.option('-o', '--output',
              default=str(Path('./layer')),
              help='target output directory',
              show_default=True)
@click.option('--dir',
              help='directory containing artifacts to bundle into a layer')
@click.option('--container',
              type=str,
              help='use the provided docker container to build the layer')
@click.argument('packages', nargs=-1)
def python(
        publisher: LayerPublisher,
        runtime: str,
        manifest,
        output,
        dir,
        container,
        packages
):
    while not runtime:
        runtime = input(f'Python runtime ({",".join(PYTHON_RUNTIMES)}): ').strip()
        if runtime not in PYTHON_RUNTIMES:
            print(f'runtime must be one of ({",".join(PYTHON_RUNTIMES)})!')

    if not manifest and not packages and not dir:
        packages = input('Python packages: ').strip().split(' ')

    runtime = runtime.replace('python', '')
    _runtime_name = f'python{runtime}'
    publisher.runtimes = [_runtime_name]
    bundler = PythonBundler(runtime=runtime,
                            artifact_dir=dir,
                            local_dir=output,
                            container=container,
                            manifest=manifest,
                            packages=packages)
    publisher.publish_layer(bundler.bundle(), _runtime_name)


@cli.command()
@click_common
@click.option('--dockerfile',
              help='use the provided dockerfile for bundling')
@click.option('-o', '--output',
              default=str(Path('./layer')),
              help='target output directory',
              show_default=True)
@click.option('-w', '--workdir',
              default='/opt',
              help='workdir used when bundling inside the container',
              show_default=True)
@click.option('-c', '--cmd',
              help='command executed inside the container; '
                   'defaults to executing the build artifact with /bin/bash')
@click.option('--base-image',
              default='amazonlinux:latest',
              help='use the provided base docker image when compiling the '
                   'Dockerfile for lambda bundling',
              show_default=True)
@click.option('-p', '--packages',
              multiple=True,
              help='additional packages to install in the container; '
                   'currently only yum is supported')
@click.option('-r', '--runtimes',
              multiple=True,
              default=['all'],
              type=click.Choice(BINARY_RUNTIMES + ['all']),
              help='compatible runtimes')
@click.argument('artifact', nargs=1, type=click.Path(exists=True))
def binary(
        publisher: LayerPublisher,
        dockerfile: str,
        output: str,
        workdir: str,
        cmd: str,
        base_image: str,
        packages: List[str],
        runtimes: List[str],
        artifact
):
    publisher.runtimes = [...[BINARY_RUNTIMES if 'all' in runtimes else runtimes]]
    bundler = BinaryBundler(build_artifact=artifact[0],
                            local_dir=output,
                            base_image=base_image,
                            yum_packages=packages,
                            dockerfile=dockerfile,
                            build_cmd=cmd,
                            workdir=workdir)
    publisher.publish_layer(bundler.bundle(), 'binary')


if __name__ == '__main__':
    docker = BinaryBundler(build_artifact='static-gnupg-build.sh')
    docker.bundle()
