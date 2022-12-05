from pathlib import Path
from abc import ABC
from typing import List, Optional
from . import docker_cmd as docker
import shutil
from .logger import logger
from .proc import path_copy


class Bundler(ABC):
    def __init__(self,
                 workdir: str = '/opt',
                 local_dir: str = './layer',
                 container_cmd: str = None,
                 container: str = None,
                 build_artifact: str = None,
                 container_output_dir: str = None):
        self.__cleanup_paths: List[Path] = []
        self.workdir = workdir
        self.local_path = Path(local_dir)
        self.build_artifact_path = Path(build_artifact) if build_artifact else None
        self.prep_local(self.local_path, self.build_artifact_path)
        self.container = container
        self.container_cmd = container_cmd
        self.container_output_dir = container_output_dir if container_output_dir else workdir

    def prep_local(self, local_path: Path, build_artifact_path: Optional[Path]):
        if not local_path.exists():
            with logger().status(f'creating layer output dir {local_path}'):
                local_path.mkdir()
                if local_path.exists():
                    logger().success(f'created layer output dir {local_path}')
                else:
                    logger().fatal_error(f'failed to create layer output directory {local_path}! Check permissions.')

        if not build_artifact_path:
            return

        if build_artifact_path.is_dir():
            if str(build_artifact_path.resolve()) != str(local_path.resolve()):
                path_copy(build_artifact_path, local_path)
        else:
            if str(build_artifact_path.parents[0].resolve()) != str(local_path.resolve()):
                path_copy(build_artifact_path, local_path)
            self.build_artifact_path = local_path / build_artifact_path.name

    def bundle(self) -> Path:
        try:
            self.pre_bundle()
            with logger().status('bundling layer with Docker...'):
                cmd_str = f'{self.container_cmd} && zip -r layer.zip *'
                if self.container_output_dir != self.workdir:
                    cmd_str = f'mkdir -p {self.container_output_dir} && ' + cmd_str
                try:
                    logger().log(f'starting bundling task with docker container {self.container}')
                    docker.run(container=self.container,
                               workdir=self.workdir,
                               volume=f'{self.local_path.absolute()}:{self.container_output_dir}',
                               container_cmd=['/bin/bash', '-c', cmd_str])
                except Exception as e:
                    logger().fatal_error(f'failed bundling layer with docker container {self.container}: {str(e)}')
                logger().success('bundling complete!')
            self.post_bundle()
            # delete all files in the output dir that are not the layer itself
            for p in self.local_path.iterdir():
                if p.name != 'layer.zip':
                    self.add_cleanup_path(p)
        finally:
            self.cleanup()
        return self.local_path / 'layer.zip'

    def add_cleanup_path(self, p: Path):
        self.__cleanup_paths.append(p)

    def cleanup(self):
        with logger().status('cleaning up...'):
            for p in self.__cleanup_paths:
                if p.is_dir():
                    logger().log(f'deleting dir: {p}')
                    shutil.rmtree(p)
                else:
                    logger().log(f'deleting file: {p}')
                    p.unlink(missing_ok=True)
            logger().success(f'cleaned up {len(self.__cleanup_paths)} file paths')

    def pre_bundle(self):
        pass

    def post_bundle(self):
        pass
