from typing import List
from .bundler import Bundler
from string import Template

PYTHON_ECR_TEMPLATE = Template('public.ecr.aws/sam/build-python${runtime}:${version}')


class PythonBundler(Bundler):

    def __init__(self,
                 runtime: str,
                 local_dir: str = './layer',
                 container: str = None,
                 packages: List[str] = None,
                 manifest: str = None):

        container_cmd = 'pip install -t python'
        if manifest:
            container_cmd += f' -r {manifest}'

        if packages:
            container_cmd += ' ' + ' '.join(packages)

        if not container:
            container = PYTHON_ECR_TEMPLATE.substitute(runtime=runtime, version='latest')

        super(PythonBundler, self).__init__(container=container,
                                            container_cmd=container_cmd,
                                            local_dir=local_dir,
                                            build_artifact=manifest)
