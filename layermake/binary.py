from typing import List, Set
from pathlib import Path
import uuid
from .cmd import docker_build
from .bundler import Bundler
from .logger import logger

# list of filenames to look for when provided a directory instead of a file as a build artifact
_build_filenames = ["build", "install", "layer", "build-layer"]

# include .sh extensions
DIR_BUILD_FILENAMES = _build_filenames.extend([f"{x}.sh" for x in _build_filenames])


class BinaryBundler(Bundler):
    """
    Bundler for binary artifacts.
    This class will attempt to find a build script
    """

    def __init__(
        self,
        build_artifact: str = None,
        base_image: str = "amazonlinux:latest",
        dockerfile: str = None,
        local_dir: str = "./layer",
        build_cmd: str = None,
        yum_packages: List[str] = None,
        workdir: str = "/opt",
        container_output_dir: str = "/opt",
        no_zip: bool = False,
    ):
        super(BinaryBundler, self).__init__(
            workdir=workdir,
            local_dir=local_dir,
            build_artifact=build_artifact,
            no_zip=no_zip,
        )
        self.__yum_packages = set(yum_packages)
        self.__yum_packages.add("gzip")
        self.__dockerfile = dockerfile
        self.__base_image = base_image
        self.__container_output_dir = container_output_dir
        if build_cmd:
            self.__container_cmd = build_cmd
            return

        with logger().status("searching for build command..."):
            if self.__build_artifact_path.is_dir():
                for p in self.__build_artifact_path.iterdir():
                    if p.name == "make":
                        # if makefile was found, use it
                        self.__container_cmd = "make install"
                        logger().info(f"found make file: {p}")
                        break
                    if p.name in DIR_BUILD_FILENAMES:
                        self.__container_cmd = f"chmod +x ./{p.name} " f"&& ./{p.name}"
                        logger().info(f"found build script: {p}")
                        break

                if not self.__container_cmd:
                    logger().fatal_error("no valid build file exists in artifact dir")
                return

            self.__container_cmd = (
                f"chmod +x ./{self.__build_artifact_path.name} "
                f"&& ./{self.__build_artifact_path.name}"
            )
            logger().debug(f"container command will be {self.__container_cmd}")

    def pre_bundle(self):
        if not self.__dockerfile:
            with logger().status("compiling docker file..."):
                dockerfile_contents = self.compile_dockerfile(
                    base_image=self.__base_image,
                    workdir=self.__workdir,
                    packages=self.__yum_packages,
                )
                logger().debug(f"compiled dockerfile contents:\n {dockerfile_contents}")
                dockerfile_path = Path(".") / f".tmp-dockerfile-{uuid.uuid4()}"
                self.__dockerfile = str(dockerfile_path.absolute())
                try:
                    with open(self.__dockerfile, "w") as f:
                        f.write(dockerfile_contents)
                except Exception as e:
                    logger().fatal_error(f"Failed to compile Dockerfile: {str(e)}")
                self.add_cleanup_path(dockerfile_path)
                logger().success(f"compiled dockerfile saved to {dockerfile_path}")

        with logger().status(
            f"building container with Dockerfile: {self.__dockerfile}..."
        ):
            build_result = docker_build(self.__dockerfile)
            container_hash = build_result.stdout.decode("utf-8").strip("\n")
            self._container = container_hash
            logger().success(f"container built successfully: {container_hash}")

    @staticmethod
    def compile_dockerfile(
        base_image: str = "amazonlinux:latest",
        workdir: str = "/opt",
        packages: Set[str] = None,
    ):
        dockerfile = f"""FROM {base_image}
ENV OUTPUT_BIN=/opt/bin
ENV OUTPUT_LIB=/opt/lib
RUN yum -y groupinstall 'Development Tools'
"""
        if packages:
            dockerfile += f"RUN yum -y install {' '.join(packages)}\n"

        dockerfile += f"""
        RUN mkdir -p {workdir}
ENTRYPOINT [""]
"""

        return dockerfile
