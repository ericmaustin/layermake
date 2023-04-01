[![PyPI version](https://badge.fury.io/py/layermake.svg)](https://badge.fury.io/py/layermake)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# LAYERMAKE

layermake is a CLI tool for creating AWS Lambda layers

layermake currently supports creating python, NodeJS, and binary layers. 

## Requirements
Currently layermake has only been tested on Python >= 3.8

## Installation:
Install from pypi: `pip install layermake`

or install from source:

git clone or download this repository and install with:
```sh
pip install .
```
The binary should now be installed and can be invoked with:

`layermake COMMAND [ARGS]`

## Usage:
run `layermake` with one of the following commands:
- `nodejs`
- `python`
- `binary`

`layermake nodejs` and `layermake python` support fully interactive layer building if no
arguments are passed.

All commands share the following options:
```
  -n, --name TEXT                 layer name
  -l, --license TEXT              text to include in the license field of the layer
  --license-file TEXT             file containing license info to include in the license field of the layer
  -a, --arch [x86_64|arm64]       architectures this layer is compatible with
  --profile TEXT                  AWS profile to use
  -d, --description TEXT          description of the layer
  -v, --verbose                   verbose output
 ```

### NodeJS bundling

To interactively bundle a NodeJS layer with defaults use:
`layermake nodejs`

All NodeJS bundling options as displayed with `layermake nodejs --help`

To use a package.json file use the option `--manifest` or `-m`:
```sh
layermake nodejs -n "my nodejs layer" -r 14.x -m package.json
```



```
Usage: layermake nodejs [OPTIONS] [PACKAGES]...

Options:
  -n, --name TEXT            layer name
  -l, --license TEXT         text to include in the license field of the layer
  --license-file TEXT        file containing license info to include in the license field of the layer
  -a, --arch [x86_64|arm64]  architectures this layer is compatible with
  --profile TEXT             AWS profile to use
  -d, --description TEXT     description of the layer
  -v, --verbose              verbose output
  --quiet                    quiet output. Only display errors and warnings. Turn off animations.
  --no-publish               do not publish the layer, only bundle.
  -r, --runtime TEXT         nodejs runtime
  -m, --manifest TEXT        nodejs manifest file (package.json)
  -o, --output TEXT          target output directory  [default: layer]
  --container TEXT           use the provided docker container to build the layer
  --dir TEXT                 directory containing artifacts to bundle into a layer
  --help                     Show this message and exit.
```

### Python bundling

To interactively bundle a Python layer with defaults use:
`layermake python`

All Python bundling options as displayed with `layermake python --help`

```
Usage: layermake python [OPTIONS] [PACKAGES]...

Options:
  -n, --name TEXT            layer name
  -l, --license TEXT         text to include in the license field of the layer
  --license-file TEXT        file containing license info to include in the license field of the layer
  -a, --arch [x86_64|arm64]  architectures this layer is compatible with
  --profile TEXT             AWS profile to use
  -d, --description TEXT     description of the layer
  -v, --verbose              verbose output
  --quiet                    quiet output. Only display errors and warnings. Turn off animations.
  --no-publish               do not publish the layer, only bundle.
  -r, --runtime TEXT         python runtime
  -m, --manifest TEXT        python manifest file (requirements.txt)
  -o, --output TEXT          target output directory  [default: layer]
  --dir TEXT                 directory containing artifacts to bundle into a layer
  --container TEXT           use the provided docker container to build the layer
  --help                     Show this message and exit.
```


### Binary bundling
Binary bundling requires an argument specifying either a build script or a directory
where either a makefile exists or one of `build`, `install`, `layer`, `build-layer` exists 
(with or without a `.sh` file extensions). If none of these files are provided, you may
pass a custom container command to run instead (e.g. `/bin/bash my_script.sh`).

When bundling a binary layer, the build script is responsible for installing 
libraries and binaries inside `/opt/bin` and/or `/opt/lib`. These directories 
are zipped inside Docker after running the build script.

Currently, only Docker images that provide `yum` package manager are supported as
`yum` is used to install build tools in the base image (defaults to `amazonlinux:latest`)

To add any prerequisite packages not installed by the build script use the `--packages` 
flag to have them installed before bundling.

Example:
```sh
layermake binary -n 'GnuPG 2.8' -p zlib gnupg-build.sh
```

```
Usage: layermake binary [OPTIONS] [ARTIFACT]...

Options:
  -n, --name TEXT                 layer name
  -l, --license TEXT              text to include in the license field of the layer
  --license-file TEXT             file containing license info to include in the license field of the layer
  -a, --arch [x86_64|arm64]       architectures this layer is compatible with
  --profile TEXT                  AWS profile to use
  -d, --description TEXT          description of the layer
  -v, --verbose                   verbose output
  --dockerfile TEXT               use the provided dockerfile for bundling
  -o, --output TEXT               target output directory  [default: layer]
  -w, --workdir TEXT              workdir used when bundling inside the container  [default: /opt]
  -c, --cmd TEXT                  command executed inside the container; defaults to executing the build artifact with /bin/bash
  --base-image TEXT               use the provided base docker image when compiling the Dockerfile for lambda bundling
                                  [default: amazonlinux:latest]
  -p, --packages TEXT             additional packages to install in the container; currently only yum is supported
  -r, --runtimes [nodejs|nodejs4.3|nodejs6.10|nodejs8.10|nodejs10.x|nodejs12.x|nodejs14.x|nodejs16.x|java8|java8.al2|java11|python2.7|python3.6|python3.7|python3.8|python3.9|dotnetcore1.0|dotnetcore2.0|dotnetcore2.1|dotnetcore3.1|dotnet6|nodejs4.3-edge|go1.x|ruby2.5|ruby2.7|provided|provided.al2|nodejs18.x|all] compatible runtimes
  --help                          Show this message and exit.
```

## Todo:
- comprehensive unit testing
- rust support
- java support