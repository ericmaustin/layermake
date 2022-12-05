from typing import List
from string import Template
from pathlib import Path
from .bundler import Bundler
from .proc import path_copy

PYTHON_ECR_TEMPLATE = Template('public.ecr.aws/sam/build-python${runtime}:${version}')


def is_package(path: Path) -> bool:
    return path.is_dir() and (path / '__init__.py').is_file()


class PythonBundler(Bundler):

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
            container = PYTHON_ECR_TEMPLATE.substitute(runtime=runtime, version='latest')

        super(PythonBundler, self).__init__(container=container,
                                            container_cmd='',
                                            local_dir=local_dir,
                                            build_artifact=manifest)

    def pre_bundle(self):
        container_cmds = []
        if self.artifact_dir and self.artifact_dir.exists():
            local_src = self.local_path / 'src'
            build_target = self.local_path / 'python'
            package_src = local_src / self.artifact_dir.name
            self.add_cleanup_path(local_src)
            # copy to package source
            path_copy(self.artifact_dir, package_src)

            if (package_src / 'requirements.txt').is_file() or (package_src / 'setup.py').is_file():
                container_cmds.append(f'pip install src/{package_src.name}/. -t python')

            if is_package(package_src):
                package_target = build_target / package_src.name
                # copy the package source as-is to build_artifact
                path_copy(package_src, package_target)
            else:
                # copy the contents of the dir straight to the build target
                path_copy(package_src, build_target)

        if self.packages or self.manifest:
            cmd = 'pip install -t python'

            if self.manifest:
                cmd += f' -r {self.manifest}'

            if self.packages:
                cmd += ' ' + ' '.join(self.packages)

            container_cmds.append(cmd)

        self.container_cmd = '; '.join(container_cmds)

