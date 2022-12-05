from setuptools import setup, find_packages
# read the contents of your README file
from pathlib import Path
from layermake import version

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='layermake',
    description='CLI toolkit for bundling AWS Lambda layers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Eric Austin',
    url='https://github.com/ericmaustin/layermake',
    license='MIT',
    author_email='eric.m.austin@gmail.com',
    python_requires='>=3.7',
    version=version,
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'Click',
        'boto3',
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'layermake = layermake.cli:cli',
        ],
    },
)