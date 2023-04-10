from typing import List
import shutil
from pathlib import Path
import boto3

from .cmd import rmtree
from .logger import logger


class LayerPublisher:
    def __init__(
        self,
        name: str,
        license_file: str = None,
        license_text: str = None,
        description: str = None,
        no_publish: bool = False,
        profile: str = None,
        arch: List[str] = None,
        no_zip: bool = False,
    ):
        boto_session = (
            boto3.Session(profile_name=profile) if profile else boto3.Session()
        )

        self.__client = boto_session.client("lambda")
        self.__name = name
        self.__license_text = license_text
        self.__license_file = Path(license_file) if license_file else None
        self.__description = description
        self.__no_pub = no_publish
        self.__no_zip = no_zip
        self.__arch = arch
        self.__runtimes = []

    @property
    def no_zip(self) -> bool:
        return self.__no_zip

    @property
    def no_publish(self) -> bool:
        return self.__no_pub

    @property
    def name(self) -> str:
        return self.__name

    def get_license_info(self) -> str:
        if self.__license_text:
            return self.__license_text
        if self.__license_text:
            with open(self.__license_text, "r") as f:
                return f.read()
        return ""

    def publish_layer(self, output_path: Path, layer_type: str):
        if not output_path.exists():
            raise FileNotFoundError(f"layer at: {output_path} is empty")

        if self.__no_zip:
            logger().info('layer publishing skipped because "--no-zip" was set')
            return

        if self.__no_pub:
            logger().info('layer publishing skipped because "--no-publish" was set')
            return

        with logger().status("publishing layer"):
            try:
                resp = self.__client.publish_layer_version(
                    LayerName=self.name,
                    Description=self.__description
                    or f"my {layer_type} layer built with layermake",
                    Content={"ZipFile": output_path},
                    LicenseInfo=self.get_license_info(),
                    CompatibleRuntimes=self.__runtimes,
                    CompatibleArchitectures=self.__arch or ["x86_64"],
                )
                logger().success(f'version: {resp["Version"]}', concat=True)
            except Exception as e:
                logger().fatal_error(f"Failed to publish layer: {str(e)}")
