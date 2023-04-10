from typing import List
from string import Template
from pathlib import Path
from .bundler import Bundler
from .cmd import path_copy
from .logger import logger

PYTHON_ECR_TEMPLATE = Template("public.ecr.aws/sam/build-python${runtime}:${version}")


def _is_package(path: Path) -> bool:
    """
    is_package checks if the path is a python package
    """
    return path.is_dir() and (path / "__init__.py").is_file()


class PythonBundler(Bundler):
    """
    PythonBundler is a bundler for python layers
    """

    def __init__(
        self,
        runtime: str,
        local_dir: Path,
        container: str = None,
        artifact_dir: str = None,
        packages: List[str] = None,
        manifest: str = None,
        no_zip: bool = False,
    ):
        self.__manifest = manifest
        self.__packages = packages
        self.__artifact_dir = Path(artifact_dir) if artifact_dir else None

        if not container:
            container = PYTHON_ECR_TEMPLATE.substitute(
                runtime=runtime, version="latest"
            )

        super(PythonBundler, self).__init__(
            workdir="/opt",
            container=container,
            container_cmd="",
            local_dir=local_dir,
            build_artifact=manifest,
            no_zip=no_zip,
        )

    def pre_bundle(self):
        container_cmds = []
        local_src = self._local_path / "src"
        try:
            local_src.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger().fatal_error(f"failed to create directory {local_src} Error: {e}")

        self.add_cleanup_path(local_src)
        build_target = self._local_path / "python"

        if self.__artifact_dir and self.__artifact_dir.exists():
            package_src = local_src / self.__artifact_dir.name
            # copy to package source
            path_copy(self.__artifact_dir, package_src)

            if (package_src / "requirements.txt").is_file() or (
                package_src / "setup.py"
            ).is_file():
                container_cmds.append(f"pip install src/{package_src.name}/. -t python")

            if _is_package(package_src):
                package_target = build_target / package_src.name
                # copy the package source as-is to build_artifact
                path_copy(package_src, package_target)
            else:
                # copy the contents of the dir straight to the build target
                path_copy(package_src, build_target)

        if self.__packages or self.__manifest:
            cmd = "pip install -t python"

            if self.__manifest:
                cmd += f" -r {Path(self.__manifest).name}"

            if self.__packages:
                cmd += " " + " ".join(self.__packages)

            container_cmds.append(cmd)

        self._container_cmd = "; ".join(container_cmds)
