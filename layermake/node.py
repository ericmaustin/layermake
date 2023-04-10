from typing import List
from string import Template
from pathlib import Path
from .bundler import Bundler
from .logger import logger
from .cmd import path_copy

NODE_ECR_TEMPLATE = Template("public.ecr.aws/sam/build-nodejs${runtime}:${version}")


def is_package(path: Path) -> bool:
    return path.is_dir() and (path / "package.json").is_file()


class NodeBundler(Bundler):
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
            container = NODE_ECR_TEMPLATE.substitute(runtime=runtime, version="latest")

        super(NodeBundler, self).__init__(
            workdir="/opt",
            container=container,
            container_cmd="",
            local_dir=local_dir,
            build_artifact=manifest,
            no_zip=no_zip,
        )

    def pre_bundle(self):
        node_dir = self._local_path / "nodejs"
        try:
            node_dir.mkdir(parents=True)
        except Exception as e:
            logger().fatal_error(f"failed to create directory {node_dir} Error: {e}")

        container_cmds = []
        if self.__artifact_dir and self.__artifact_dir.exists():
            local_src = self._local_path / "src"
            node_packages = node_dir / "node_modules"
            package_src = node_dir / self.__artifact_dir.name
            self.add_cleanup_path(local_src)
            # copy to package source
            path_copy(self.__artifact_dir, package_src)

            if is_package(package_src):
                package_target = node_packages / package_src.name
                # copy the package source as-is to build_artifact
                path_copy(package_src, package_target)
                container_cmds.append(
                    f"pushd nodejs/node_modules/{package_target.name};"
                    f"npm install --prefix ../../;"
                    f"popd;"
                )

            else:
                path_copy(package_src, local_src)

        if self.__packages or self.__manifest:
            cmd = "pushd nodejs;"
            if self.__manifest:
                cmd += f" npm install;"

            if self.__packages:
                cmd += " npm install --save " + " ".join(self.__packages) + ";"

            cmd += "popd"
            container_cmds.append(cmd)

        self._container_cmd = "; ".join(container_cmds)
