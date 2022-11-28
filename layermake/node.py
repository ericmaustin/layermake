from typing import List
from .bundler import Bundler
from string import Template
from .logger import logger

NODE_ECR_TEMPLATE = Template('public.ecr.aws/sam/build-nodejs${runtime}:${version}')


class NodeBundler(Bundler):

    def __init__(self,
                 runtime: str,
                 local_dir: str = './layer',
                 container: str = None,
                 packages: List[str] = None,
                 manifest: str = None):

        container_cmd = 'pushd nodejs;'
        if manifest:
            container_cmd += f' npm install;'

        if packages:
            container_cmd += ' npm install --save ' + ' '.join(packages)

        container_cmd += ';popd'

        if not container:
            container = NODE_ECR_TEMPLATE.substitute(runtime=runtime, version='latest')

        super(NodeBundler, self).__init__(container=container,
                                          container_cmd=container_cmd,
                                          local_dir=local_dir,
                                          build_artifact=manifest)

    def pre_bundle(self):
        node_dir = self.local_path / 'nodejs'
        if node_dir.exists():
            return

        with logger().status(f'creating nodejs output dir: {node_dir}...'):
            node_dir.mkdir()
            if node_dir.exists():
                logger().success(f'created {node_dir}')
            else:
                logger().fatal_error(f'failed to create directory {node_dir}! Check permissions.')
