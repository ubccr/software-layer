#!/bin/bash
#
# Build container for CCR software layer.
#
# Runs a singularity container, mounts CCR cvmfs repo with a writable overlay
# and starts a shell.
#
# This file was adopted from https://github.com/EESSI/software-layer/blob/main/build_container.sh
# Distributed under the terms of the GNU General Public License v2.0.
#
# Modifications made by CCR are also released under GPLv2. 
#

display_help() {
  echo "usage: $0 [OPTIONS] <path to temporary dir>"
  echo " OPTIONS:"
  echo "  -h | --help            - display help"
  echo "  -p | --prefix          - run gentoo startprefix.sh"
  echo "  -s | --shell           - start singularity shell"
  echo "  -r | --run CMD         - exec CMD in container"
}

LONGOPTS=help,prefix,shell,run:
OPTIONS=hpsr:
PARSED_ARGS=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
if [[ $? -ne 0 ]]; then
    exit 1;
fi

eval set -- "$PARSED_ARGS"

RUN_PREFIX=n
RUN_SHELL=n
RUN_CMD=
while [ : ]; do
  case "$1" in
    -h | --help)
        display_help
        exit 0
        ;;
    -p | --prefix)
        RUN_PREFIX=y
        shift
        ;;
    -s | --shell)
        RUN_SHELL=y
        shift
        ;;
    -r | --run)
        RUN_CMD="$2"
        shift 2
        ;;
    --) shift;
        break
        ;;
  esac
done

if [[ $# -ne 1 ]]; then
    echo "ERROR: A path to a temporary dir is required."
    echo ""
    display_help
    exit 2
fi

CCR_TMPDIR=$1

. /etc/os-release

BUILD_TAG="${BUILD_TAG:-$ID$VERSION_ID}"

# XXX Only run on supported distros for now..
if [[ "$BUILD_TAG" != "ubuntu20.04" && "$BUILD_TAG" != "ubuntu22.04" && "$BUILD_TAG" != "flatcar3227.0.0" ]]; then
    echo "Unsupported linux distro: $BUILD_TAG" >&2
    exit 1
fi

CCR_CPU_FAMILY=`uname -m`

# Use pre-built CCR local container if available else fetch from dockerhub
if [ -f "/util/software/containers/${CCR_CPU_FAMILY}/${BUILD_TAG}.sif" ]; then
    BUILD_CONTAINER="/util/software/containers/${CCR_CPU_FAMILY}/${BUILD_TAG}.sif"
else
    BUILD_CONTAINER="docker://ubccr/build-node:$BUILD_TAG"
fi

CVMFS_CONFIG_REPO="cvmfs-config.ccr.buffalo.edu"
CVMFS_SOFT_REPO="soft.ccr.buffalo.edu"
CCR_VERSION=${CCR_VERSION:-2023.01}

if [ ! -d "/cvmfs/$CVMFS_SOFT_REPO/versions/$CCR_VERSION" ]; then
    echo "ERROR: cvmfs not mounted for CCR_VERSION=$CCR_VERSION" >&2
    exit 1
fi

echo "Running container: $BUILD_CONTAINER.."

# make sure specified temporary directory exists
mkdir -p $CCR_TMPDIR

# make sure that specified location has support for extended attributes,
# since that's required by CernVM-FS
command -v attr &> /dev/null
if [ $? -eq 0 ]; then
    testfile=$(mktemp -p $CCR_TMPDIR)
    attr -s test -V test $testfile > /dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: $CCR_TMPDIR does not support extended attributes!" >&2
        exit 2
    else
        rm $testfile
    fi
else
    echo "WARNING: 'attr' command not available, so can't check support for extended attributes..." >&2
fi

echo "Using $CCR_TMPDIR as parent for temporary directories..."

# create temporary directories
mkdir -p $CCR_TMPDIR/{home,overlay-upper,overlay-work}
mkdir -p $CCR_TMPDIR/{var-lib-cvmfs,var-run-cvmfs,tmp}

# use tmp dir
export TMPDIR=$CCR_TMPDIR/tmp

# configure Singularity
export SINGULARITY_HOME="$CCR_TMPDIR/home:/home/$USER"
export SINGULARITY_CACHEDIR=$CCR_TMPDIR/singularity_cache
SINGULARITY_BIND="$PWD:/srv/software-layer,$CCR_TMPDIR/var-run-cvmfs:/var/run/cvmfs,$CCR_TMPDIR/var-lib-cvmfs:/var/lib/cvmfs,$CCR_TMPDIR"

if [ -d "/opt/software" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},/opt/software:/opt/software:ro"
fi

if [ -d "/usr/lib/${CPU_FAMILY}-linux-gnu" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},/usr/lib/${CPU_FAMILY}-linux-gnu:/usr/lib/${CPU_FAMILY}-linux-gnu/:ro"
fi

if [ -d "/util" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},/util:/util:ro"
fi

if [ -d "/projects" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},/projects:/projects:ro"
fi

if [ -d "/etc/glvnd" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},/etc/glvnd:/etc/glvnd:rw"
fi

if [ -d "${HOME}/testsuite/sanitarium" ]; then
    SINGULARITY_BIND="${SINGULARITY_BIND},${HOME}/testsuite:/home/${USER}/testsuite:rw"
fi

export SINGULARITY_BIND

export SINGULARITYENV_CCR_VERSION=${CCR_VERSION}
export SINGULARITYENV_CCR_COMPAT_VERSION=${CCR_VERSION}
export SINGULARITYENV_LMOD_SYSTEM_DEFAULT_MODULES="ccrsoft/${CCR_VERSION}"

# set environment variables for fuse mounts in Singularity container
export CVMFS_CONFIG="container:cvmfs2 ${CVMFS_CONFIG_REPO} /cvmfs/${CVMFS_CONFIG_REPO}"
export CVMFS_READONLY="container:cvmfs2 ${CVMFS_SOFT_REPO} /cvmfs_ro/${CVMFS_SOFT_REPO}"
export CVMFS_WRITABLE_OVERLAY="container:fuse-overlayfs -o lowerdir=/cvmfs_ro/${CVMFS_SOFT_REPO} -o upperdir=$CCR_TMPDIR/overlay-upper -o workdir=$CCR_TMPDIR/overlay-work /cvmfs/${CVMFS_SOFT_REPO}"

if [ "$RUN_SHELL" == "y" ]; then
    echo "Starting Singularity shell..."
    singularity shell --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER
elif [ "$RUN_PREFIX" == "y" ]; then
    echo "Running gentoo prefix shell..."
    if [ "$CCR_VERSION" = "2023.01" ]; then
        start_prefix=/cvmfs/${CVMFS_SOFT_REPO}/versions/${CCR_VERSION}/compat/startprefix
    else
        start_prefix=/cvmfs/${CVMFS_SOFT_REPO}/versions/${CCR_VERSION}/compat/linux/${CCR_CPU_FAMILY}/startprefix
    fi

    singularity exec --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER "$start_prefix"
elif [ ! -z "$RUN_CMD" ]; then
    echo "Running '$RUN_CMD' in Singularity build container..."
    singularity exec --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER "$RUN_CMD"
else
    export SINGULARITYENV_PS1="(v${CCR_VERSION}) \[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] "
    singularity exec --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER bash --rcfile /cvmfs/${CVMFS_SOFT_REPO}/config/profile/bash.sh
fi
