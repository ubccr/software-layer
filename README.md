# CCR Software Layer

This is the CCR software layer.

_NOTE: these docs are currently very much a WIP_

## About

All software at CCR is built using [easybuild](https://docs.easybuild.io/en/latest/),
available via modules using [Lmod](https://lmod.readthedocs.io/en/latest/), and 
distributed using [CernVM-FS](https://cvmfs.readthedocs.io/en/stable/).  This repositoryl 
contains scripts to help build software with easybuild using containers. To ensure all
software runs on any compute node regardless of the underlying Linux distro, we
use [Gentoo Prefix](https://wiki.gentoo.org/wiki/Project:Prefix) as the
compatibility layer. For more information on CCR's compatibility layer see our
[gentoo-overlay](https://github.com/ubccr/gentoo-overlay).

## Building Software

Software at CCR is distributed via CernVM-FS, a read-only file system designed
to deliver scientific software. CCR's workflow for building new software uses
singularity containers with a writable overlay on top of the CCR CernVM-FS
repository. Any physical compute node can be used to run the container and
build software.

### Quick start

```
# Clone repo and start container
user@host$ git clone https://github.com/ubccr/software-layer.git
user@host$ cd software-layer
user@host$ ./start-container.sh prefix /scratch/username_somepackage

# Inside container source init scripts and run easybuild
user@container$ cd /srv/software-layer
user@container$ source config/profile/bash.sh
user@container$ source config/easybuild/init.sh
user@container$ module load easybuild
user@container$ eb --show-config
user@container$ eb --search OpenMPI
user@container$ eb OpenBLAS-0.3.9-GCC-9.3.0.eb --robot
user@container$ module load openblas
user@container$ exit

# Exit container and create tarball for ingestion into CernVM-FS
user@host$ ./create-tarball.sh easybuild /scratch/username_somepackage
user@host$ cp /scratch/ccr-xxx-easybuild-user_somepackage-xxx.tar.gz /path/to/mirrors 
```

### Workflow in detail

1. Clone this repo (or clone your own fork if you plan on submitting PRs):

```
$ git clone https://github.com/ubccr/software-layer.git
$ cd software-layer
```

2. Start a singularity container. We use the helper script `start-container.sh`
which takes an action as the first argument: `shell`, `run`, or `prefix`). The
`prefix` action starts a singularity then runs $EPREFIX/startprefix which puts
you in a gentoo prefix shell. The second argument is the path to a working
directory where the writable-overlay will write your files. This should be
somehwere in `/scratch`. It's recommended to follow a basic naming convention,
for example if your building OpenMPI, then use `/scratch/username_OpenMPI`.

```
$ ./start-container.sh prefix /scratch/username_somepackage
```

NOTE: The first time you run this command it will fetch the build-node docker
image from docker hub, convert it to singularity sif format, then start the
container. 

3. After the container starts you have a shell setup to point at the gentoo
compatibility layer. The current directory (this software-layer git repo where
you ran the start-container.sh script) is bind mounted into
`/srv/software-layer` inside the container. So cd into this directory:

```
$ cd /srv/software-layer
```

4. Fetch the latest development builds for testing. These are tarballs of
software that others have built and are ready for testing. This ensures you're
running the latest snapshot of what will be the production software:

```
$ ./fetch-dev-tarballs.sh 
```

5. Source CCR's init scripts to setup your enviroment. This will also setup
lmod and the necessary easybuild config settings used at CCR:

```
$ source config/profile/bash.sh
$ source config/easybuild/init

# This should now show the latest software modules
$ module avail
```

NOTE: You can make changes to the config/init scripts and test them inside the
container. Then commit and submit a PR's etc.


6. Load the easybuild module:

```
$ module load easybuild
```

7. Build software, test software:

```
$ eb OpenBLAS-0.3.9-GCC-9.3.0.eb --robot
[grab a cup of coffee]
...
[hours later]
..
$ module load openblas
$ exit
```

8. Once you exit the container terminated and any easybuild files (modules,
software) that were written to `/cvmfs` were captured in your workdir in a
directory named `overlay-upper`. We can now run a script to tar up these files
for eventual importing into the CCR cvmfs repo. The tarball will be created
with the following naming convention:

```
 ccr-<version>-{compat,easybuild,config}-[some tag]-<timestamp>.tar.gz
```

To create a tarball after building software with easybuild run:

```
$ ./create-tarball.sh easybuild /scratch/username_somepackage
```

9. Copy the resulting tarball to mirrors so that others can test out your work
before publishing to our productuion CernVM-FS stratum0 server.

## Re-building the build-node container image

The build-node docker container image is currently hosted on [docker hub](https://hub.docker.com/r/ubccr/build-node).
To build a new container image run:

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


## License

The software in this repository is distributed under the terms of the GNU
General Public License v2.0. See the LICENSE file.
