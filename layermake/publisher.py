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

    def publish_layer(self, output_path: Path, zip_target: Path, layer_type: str):
        if self.__no_zip:
            logger().info('layer publishing and zipping skipped with "--no-zip"')
            return

        if not output_path.is_dir():
            raise NotADirectoryError(f"layer output directory: {output_path} not found")

        with logger().status("zipping layer"):
            logger().info(f"zipping layer contents in: {output_path}")
            shutil.make_archive(str(output_path), "zip", str(zip_target))
            logger().success(f"zipped layer contents in: {output_path} to {zip_target}")

        if not zip_target.exists():
            raise FileNotFoundError(f"layer zip file: {zip_target} is empty")

        # delete the output directory after zipping
        with logger().status("removing layer source directory"):
            logger().info(f"deleting dir: {output_path}")
            rmtree(output_path)

        if self.__no_pub:
            logger().info('layer publishing skipped with "--no-publish"')
            return

        with logger().status("publishing layer"):
            try:
                resp = self.__client.publish_layer_version(
                    LayerName=self.name,
                    Description=self.__description
                    or f"my {layer_type} layer built with layermake",
                    Content={"ZipFile": zip_target},
                    LicenseInfo=self.get_license_info(),
                    CompatibleRuntimes=self.__runtimes,
                    CompatibleArchitectures=self.__arch or ["x86_64"],
                )
                logger().success(f'version: {resp["Version"]}', concat=True)
            except Exception as e:
                logger().fatal_error(f"Failed to publish layer: {str(e)}")
