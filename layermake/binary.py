from typing import List
from pathlib import Path
import uuid
from . import docker_cmd as docker
from .bundler import Bundler
from .logger import logger

DEFAULT_PACKAGES = ['gzip']

# list of filenames to look for when provided a directory instead of a file as a build artifact
DIR_BUILD_FILENAMES = ['build', 'install', 'layer', 'build-layer']
# include .sh extensions
DIR_BUILD_FILENAMES = DIR_BUILD_FILENAMES.extend([f'{x}.sh' for x in DIR_BUILD_FILENAMES])


class BinaryBundler(Bundler):
    def __init__(self,
                 build_artifact: str = None,
                 base_image: str = 'amazonlinux:latest',
                 dockerfile: str = None,
                 local_dir: str = './layer',
                 build_cmd: str = None,
                 yum_packages: List[str] = None,
                 workdir: str = '/opt',
                 container_output_dir: str = '/opt'):

        super(BinaryBundler, self).__init__(workdir=workdir,
                                            local_dir=local_dir,
                                            build_artifact=build_artifact)
        self.yum_packages = yum_packages if yum_packages else []
        self.dockerfile = dockerfile
        self.base_image = base_image
        self.container_output_dir = container_output_dir
        if not build_cmd:
            with logger().status('searching for build command...'):
                if self.build_artifact_path.is_dir():
                    for p in self.build_artifact_path.iterdir():
                        if p.name == 'make':
                            # if makefile was found, use it
                            self.container_cmd = 'make install'
                            logger().log(f'found make file: {p}')
                            break
                        if p.name in DIR_BUILD_FILENAMES:
                            self.container_cmd = f'chmod +x ./{p.name} ' \
                                                 f'&& ./{p.name}'
                            logger().log(f'found build script: {p}')
                            break

                    if not self.container_cmd:
                        logger().fatal_error('no valid build file exists in artifact dir')
                else:
                    self.container_cmd = f'chmod +x ./{self.build_artifact_path.name} ' \
                                         f'&& ./{self.build_artifact_path.name}'
                    logger().debug(f'container command will be {self.container_cmd}')
        else:
            self.container_cmd = build_cmd

    def pre_bundle(self):
        packages = [x for x in self.yum_packages if x not in DEFAULT_PACKAGES]
        packages.extend(DEFAULT_PACKAGES)

        if not self.dockerfile:
            with logger().status('compiling docker file...'):
                dockerfile_contents = self.compile_dockerfile(base_image=self.base_image,
                                                              workdir=self.workdir,
                                                              packages=packages)
                logger().debug(f'compiled dockerfile contents:\n {dockerfile_contents}')
                dockerfile_path = Path('.') / f'.tmp-dockerfile-{uuid.uuid4()}'
                self.dockerfile = str(dockerfile_path.absolute())
                try:
                    with open(self.dockerfile, 'w') as f:
                        f.write(dockerfile_contents)
                except Exception as e:
                    logger().fatal_error(f'Failed to compile Dockerfile: {str(e)}')
                self.add_cleanup_path(dockerfile_path)
                logger().success(f'compiled dockerfile saved to {dockerfile_path}')

        with logger().status(f'building container with Dockerfile: {self.dockerfile}...'):
            build_result = docker.build(self.dockerfile)
            container_hash = build_result.stdout.decode('utf-8').strip('\n')
            self.container = container_hash
            logger().success(f'container built successfully: {container_hash}')

    @staticmethod
    def compile_dockerfile(base_image: str = 'amazonlinux:latest',
                           workdir: str = '/opt',
                           packages: List[str] = None):
        if not packages:
            packages = ['gzip']

        dockerfile = f"""FROM {base_image}
ENV OUTPUT_BIN=/opt/bin
ENV OUTPUT_LIB=/opt/lib
RUN yum -y groupinstall 'Development Tools'
RUN yum -y install {' '.join(packages)}
RUN mkdir -p {workdir}
ENTRYPOINT [""]
"""
        return dockerfile
