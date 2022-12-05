from typing import List
from string import Template
from pathlib import Path
from .bundler import Bundler
from .logger import logger
from .proc import path_copy

NODE_ECR_TEMPLATE = Template('public.ecr.aws/sam/build-nodejs${runtime}:${version}')


def is_package(path: Path) -> bool:
    return path.is_dir() and (path / 'package.json').is_file()


class NodeBundler(Bundler):

    def __init__(self,
                 runtime: str,
                 local_dir: str = './layer',
                 container: str = None,
                 artifact_dir: str = None,
                 packages: List[str] = None,
                 manifest: str = None):

        self.manifest = manifest
        self.packages = packages
        self.artifact_dir = Path(artifact_dir) if artifact_dir else None

        if not container:
            container = NODE_ECR_TEMPLATE.substitute(runtime=runtime, version='latest')

        super(NodeBundler, self).__init__(container=container,
                                          container_cmd='',
                                          local_dir=local_dir,
                                          build_artifact=manifest)

    def pre_bundle(self):
        node_dir = self.local_path / 'nodejs'
        if node_dir.exists():
            return

        try:
            node_dir.mkdir()
        except Exception as e:
            logger().fatal_error(f'failed to create directory {node_dir} Error: {e}')

        container_cmds = []
        if self.artifact_dir and self.artifact_dir.exists():
            local_src = self.local_path / 'src'
            node_packages = node_dir / 'node_modules'
            package_src = node_dir / self.artifact_dir.name
            self.add_cleanup_path(local_src)
            # copy to package source
            path_copy(self.artifact_dir, package_src)

            if is_package(package_src):
                package_target = node_packages / package_src.name
                # copy the package source as-is to build_artifact
                path_copy(package_src, package_target)
                container_cmds.append(f'pushd nodejs/node_modules/{package_target.name};'
                                      f'npm install --prefix ../../;'
                                      f'popd;')

            else:
                path_copy(package_src, node_dir)

        if self.packages or self.manifest:
            cmd = 'pushd nodejs;'
            if self.manifest:
                cmd += f' npm install;'

            if self.packages:
                cmd += ' npm install --save ' + ' '.join(self.packages)

            cmd += ';popd'
            container_cmds.append(cmd)

        self.container_cmd = '; '.join(container_cmds)


