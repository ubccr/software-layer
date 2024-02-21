# CCR Software Layer

This is the CCR software layer.

_NOTE: these docs are currently very much a WIP_

## About

All software at CCR is built using [easybuild](https://docs.easybuild.io/en/latest/),
available via modules using [Lmod](https://lmod.readthedocs.io/en/latest/), and 
distributed using [CernVM-FS](https://cvmfs.readthedocs.io/en/stable/).  This repository 
contains scripts to help build software with easybuild using containers. To ensure all
software runs on any compute node regardless of the underlying Linux distro, we
use [Gentoo Prefix](https://wiki.gentoo.org/wiki/Project:Prefix) as the
compatibility layer. For more information on CCR's compatibility layer see our
[gentoo-overlay](https://github.com/ubccr/gentoo-overlay).

## Submitting Software Build Requests and Bug Reports  

CCR users should submit build requests for staff to install software using [GitHub issues](https://github.com/ubccr/software-layer/issues).  When creating a new issue you'll be prompted to select a template.  Requests for software builds require a link to the software website so we can ensure we're building the software you want.  We ask for a preferred software version.  We will do our best to build what you request but it may not always be possible.  Please enter a new request for each piece of software you'd like installed.  If you see a request for software already submitted that you would also like to use, please "like" the GitHub issue or comment on it.  This helps us to prioritize the build requests.

If you experience an issue with an installed module on CCR's systems, please enter a bug report.  If you need assistance with using a particular software module, running jobs, or anything else related to CCR's systems, please submit a [help request](https://www.buffalo.edu/ccr/support.html) using our ticketing system.  Bug reports should only be submitted for problems with the software installation or Easybuild system itself.    

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
user@container$ module load easybuild

# Show easybuild config
user@container$ eb --show-config

# Search for package showing short names
user@container$ eb -S OpenMPI

# Search for package showing full path to eb file
user@container$ eb --search OpenMPI

# Show the deps that will be built without actually building
user@container$ eb OpenBLAS-0.3.9-GCC-9.3.0.eb -M

# Build package and all deps
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
somewhere in `/scratch`. It's recommended to follow a basic naming convention,
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

4. Source CCR's init scripts to setup your environment:

```
$ source config/profile/bash.sh

# This should now show the latest software modules
$ module avail
```

NOTE: You can make changes to the config/init scripts and test them inside the
container. Then commit and submit a PR's etc.


5. Load the easybuild module:

```
$ module load easybuild
```

6. Build software, test software:

```
$ eb OpenBLAS-0.3.9-GCC-9.3.0.eb --robot
[grab a cup of coffee]
...
[hours later]
..
$ module load openblas
$ exit
```

7. Once you exit the container terminated and any easybuild files (modules,
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

8. Copy the resulting tarball to mirrors so that others can test out your work
before publishing to our production CernVM-FS stratum0 server.

## See Also

The config files and scripts in this repo were heavily adopted from [EESSI](https://github.com/EESSI) 
and [Compute Canada](https://github.com/ComputeCanada). You can check out their configs here:

- https://github.com/EESSI/software-layer
- https://github.com/ComputeCanada/easybuild-computecanada-config


## License

The software in this repository is distributed under the terms of the GNU
General Public License v2.0. See the LICENSE file.
