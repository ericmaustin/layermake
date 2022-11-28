import click
from functools import wraps
from typing import List
from pathlib import Path
import boto3
from .logger import set_logger, logger


class LayerPublisher:
    def __init__(self,
                 name: str,
                 license_file: str = None,
                 license_text: str = None,
                 description: str = None,
                 profile: str = None,
                 arch: List[str] = None):

        boto_session = boto3.Session(profile_name=profile) if \
            profile else boto3.Session()

        self._client = boto_session.client('lambda')
        self.name = name
        self._license_text = license_text
        self._license_file = Path(license_file) if license_file else None
        self._description = description
        self._arch = arch
        self.runtimes = []

    def get_license_info(self) -> str:
        if self._license_text:
            return self._license_text
        if self._license_text:
            with open(self._license_text, 'r') as f:
                return f.read()
        return ''

    def publish_layer(self, zip_file: Path, layer_type: str):
        if not zip_file.exists():
            raise FileNotFoundError(f'layer zip file: {zip_file} not found')

        with open(zip_file, 'rb') as f:
            zip_contents = f.read()

        if not zip_contents:
            raise FileNotFoundError(f'layer zip file: {zip_file} is empty')

        with logger().status('publishing layer'):
            try:
                resp = self._client.publish_layer_version(
                    LayerName=self.name,
                    Description=self._description or f'my {layer_type} layer built with layermake',
                    Content={
                        'ZipFile': zip_contents
                    },
                    LicenseInfo=self.get_license_info(),
                    CompatibleRuntimes=self.runtimes,
                    CompatibleArchitectures=self._arch or ['x86_64']
                )
                logger().success(f'version: {resp["Version"]}', concat=True)
            except Exception as e:
                logger().fatal_error(f'Failed to publish layer: {str(e)}')


def click_common(f):
    """
    adds common options to all commands
    """
    @click.option('-n', '--name',
                  help='layer name',
                  prompt='Layer name')
    @click.option('-l', '--license',
                  help='text to include in the license field of the layer')
    @click.option('--license-file',
                  help='file containing license info to include in the license field of the layer')
    @click.option('-a', '--arch',
                  multiple=True,
                  type=click.Choice(['x86_64', 'arm64']),
                  default=['x86_64'],
                  help='architectures this layer is compatible with')
    @click.option('--profile',
                  type=str,
                  help='AWS profile to use')
    @click.option('-d', '--description',
                  type=str,
                  help='description of the layer')
    @click.option('-v', '--verbose',
                  is_flag=True,
                  help='verbose output')
    @wraps(f)
    def new_func(name, license, license_file, arch, profile, description, verbose, *args, **kwargs):
        set_logger(verbose)
        publisher = LayerPublisher(name=name,
                                   license_text=license,
                                   license_file=license_file,
                                   profile=profile,
                                   arch=arch,
                                   description=description)
        return f(publisher, *args, **kwargs)

    return new_func
