#!/bin/bash

# Create a tarball containing easybuild modules/software, compatibility layer
# files, or config files for ingestion into the CCR CVMFS software repository.
#
# This script assumes you've used start-container.sh to install software or
# create the overlay files.

# The tarball will be created with the following naming convention:
#  ccr-<version>-{compat,easybuild,config}-[some tag]-<timestamp>.tar.gz
#
# This script was adopted from EESSI:
#  https://github.com/EESSI/software-layer/blob/main/create_tarball.sh

set -e

function echo_green() {
    echo -e "\e[32m$1\e[0m"
}

function echo_red() {
    echo -e "\e[31m$1\e[0m"
}

function echo_yellow() {
    echo -e "\e[33m$1\e[0m"
}

function fatal_error() {
    echo_red "ERROR: $1" >&2
    exit 1
}

if [[ $# -lt 2 ]]; then
    fatal_error "Usage: $0 <compat|easybuild|config> </scratch/path/to/workdir>"
fi

content_type=$1
workdir=$2

# Check if the content-type is compat, easybuild, or config
if [ "${content_type}" != "compat" ] && [ "${content_type}" != "easybuild" ] && [ "${content_type}" != "config" ]
then
    fatal_error "Content type should be either compat, easybuild, or config."
fi

if [[ -z "$CCR_VERSION" ]]; then
    fatal_error "Missing CCR_VERSION env variable."
fi

# Check if the CCR_VERSION number is valid, i.e. matches the format YYYY.DD
if ! echo "${CCR_VERSION}" | egrep -q '^20[0-9][0-9]\.(0[0-9]|1[0-2])$'
then
    fatal_error "${CCR_VERSION} is not a valid CCR version."
fi

overlay_upper_dir="${workdir}/overlay-upper"
dir_overlay="${overlay_upper_dir}/versions/${CCR_VERSION}/${content_type}"

if [ ! -d ${dir_overlay} ]; then
    fatal_error "CCR overlay directory ${dir_overlay} does not exist?!"
fi

tmpdir=`mktemp -d`

files_list=${tmpdir}/files.list.txt

cd ${overlay_upper_dir}/versions
echo ">> Collecting list of files/directories to include in tarball via ${PWD}..."

if [ -d ${CCR_VERSION}/${content_type} ]; then
    find ${CCR_VERSION}/${content_type} -type f ! -path "*/.wh..wh..opq" >> ${files_list}
    find ${CCR_VERSION}/${content_type} -type l >> ${files_list}
fi

if ! [ -s "${files_list}" ]; then
    fatal_error "No files or directories found to inlcude in tarball?"
fi

outdir=`dirname $workdir`
tag=`basename $workdir`
ts=`date "+%Y-%m-%d.%H%M%S"`
target_tgz="${outdir}/ccr-${CCR_VERSION}-${content_type}-${tag}-${ts}.tar.gz"

echo ">> Creating tarball: ${target_tgz}"
tar cfz ${target_tgz} --files-from=${files_list}

echo ${target_tgz} created!

echo ">> Cleaning up tmpdir"
rm -r ${tmpdir}
