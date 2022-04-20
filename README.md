# CCR Software Layer

This is the CCR software layer.

## About

To ensure all software runs on any compute node no matter what OS distro is
installed, we use [Gentoo Prefix](https://wiki.gentoo.org/wiki/Project:Prefix)
as the compatability layer. All software is built using easybuild and available
via modules using Lmod. This repository contains scripts to help build software
with easybuild using containers.

## Usage

_NOTE: these are currently very much a WIP_

## Building the build-node container image

The build-node docker container image is currently hosted on docker hub. To
build a new container image run:

1. Build container image:

```
$ docker build -t ubccr/build-node:debian10 -f Dockerfile.CCR-build-node-debian10 .
```

2. Push container up to docker hub:

```
# If you haven't previously authenticated, you need to do that first
$ docker login -u USERNAME

$ docker push ubccr/build-node:debian10
```

## See Also

The config files and scripts in this repo were heavily adopted from [EESSI](https://github.com/EESSI) 
and [Compute Canada](https://github.com/ComputeCanada). You can check out their configs here:

- https://github.com/EESSI/software-layer
- https://github.com/ComputeCanada/easybuild-computecanada-config
