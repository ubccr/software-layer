#!/bin/bash
#
# Build container for CCR software layer.
#
# Runs a singularity container, mounts CCR cvmfs repo with a writable overlay
# and starts a gentoo prefix shell.
#
# This file was adopted from https://github.com/EESSI/software-layer/blob/main/build_container.sh
# Distributed under the terms of the GNU General Public License v2.0.
#
# Modifications made by CCR are also released under GPLv2. 
#

. /etc/os-release

BUILD_TAG="${BUILD_TAG:-$ID$VERSION_ID}"

# XXX Only run on supported distros for now..
if [[ "$BUILD_TAG" != "ubuntu20.04" && "$BUILD_TAG" != "ubuntu22.04" && "$BUILD_TAG" != "flatcar3227.0.0" && "$BUILD_TAG" != "centos7" ]]; then
    echo "Unsupported linux distro: $BUILD_TAG" >&2
    exit 1
fi

# Use pre-built CCR local container if available else fetch from dockerhub
if [ -f "/util/software/containers/${BUILD_TAG}.sif" ]; then
    BUILD_CONTAINER="/util/software/containers/${BUILD_TAG}.sif"
else
    BUILD_CONTAINER="docker://ubccr/build-node:$BUILD_TAG"
fi

CVMFS_CONFIG_REPO="cvmfs-config.ccr.buffalo.edu"
CVMFS_SOFT_REPO="soft.ccr.buffalo.edu"
CCR_VERSION=${CCR_VERSION:-2023.01}

if [ $# -lt 2 ]; then
    echo "Usage: $0 <shell|run|prefix> <path to work directory>" >&2
    exit 1
fi
ACTION=$1
CCR_TMPDIR=$2
shift 2

if [ "$ACTION" == "run" ] && [ $# -eq 0 ]; then
    echo "ERROR: No command specified to run?!" >&2
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

# set environment variables for fuse mounts in Singularity container
export CVMFS_CONFIG="container:cvmfs2 ${CVMFS_CONFIG_REPO} /cvmfs/${CVMFS_CONFIG_REPO}"
export CVMFS_READONLY="container:cvmfs2 ${CVMFS_SOFT_REPO} /cvmfs_ro/${CVMFS_SOFT_REPO}"
export CVMFS_WRITABLE_OVERLAY="container:fuse-overlayfs -o lowerdir=/cvmfs_ro/${CVMFS_SOFT_REPO} -o upperdir=$CCR_TMPDIR/overlay-upper -o workdir=$CCR_TMPDIR/overlay-work /cvmfs/${CVMFS_SOFT_REPO}"

if [ "$ACTION" == "shell" ]; then
    echo "Starting Singularity build container..."
    singularity shell --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER
elif [ "$ACTION" == "run" ]; then
    echo "Running '$@' in Singularity build container..."
    singularity exec --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER "$@"
elif [ "$ACTION" == "prefix" ]; then
    echo "Running gentoo prefix shell in Singularity build container..."
    singularity exec --fusemount "$CVMFS_CONFIG" --fusemount "$CVMFS_READONLY" --fusemount "$CVMFS_WRITABLE_OVERLAY" $BUILD_CONTAINER /cvmfs/${CVMFS_SOFT_REPO}/versions/${CCR_VERSION}/compat/startprefix
else
    echo "ERROR: Unknown action specified: $ACTION (should be either 'shell', 'run', or 'prefix')" >&2
    exit 1
fi
