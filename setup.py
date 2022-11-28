from setuptools import setup, find_packages

setup(
    name='layermake: Lambda Layer bundling tool',
    python_requires='>=3.8',
    version='0.0.1',
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