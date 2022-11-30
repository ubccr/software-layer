#!/usr/bin/env bash
#
# Install gentoo prefix compatability layer
#
# This should be runs inside a singularity container that mounts CCR cvmfs repo
# with a writable overlay
#
# Distributed under the terms of the GNU General Public License v2
#

set -e

function echo_red() {
    echo -e "\e[31m$1\e[0m"
}

function fatal_error() {
    echo_red "ERROR: $1" >&2
    exit 1
}

function install_prefix() {
    local ccr_compat="$1"
    if [[ -d "${ccr_compat}" ]]; then
        fatal_error "Directory already exists: $ccr_compat"
    fi

    # Create gentoo prefix path
    mkdir -p ${ccr_compat}/etc/portage/package.mask

    # Mask gcc package to ensure gcc10 is installed
    tee ${ccr_compat}/etc/portage/package.mask/gcc <<EOF
>=sys-devel/gcc-11
EOF

    # Fetch gentoo prefix bootstrap script
    wget -O /tmp/bootstrap-prefix.sh https://gitweb.gentoo.org/repo/proj/prefix.git/plain/scripts/bootstrap-prefix.sh
    chmod +x /tmp/bootstrap-prefix.sh

    # This needs to be unset or bootstrap is grumpy
    unset LD_LIBRARY_PATH

    # Run gentoo prefix bootstrap stages 1-3 ensuring we use all available cores
    num_procs=$(cat /proc/cpuinfo | grep processor | wc -l)
    USE_CPU_CORES=$num_procs STOP_BOOTSTRAP_AFTER=stage3 /tmp/bootstrap-prefix.sh $ccr_compat noninteractive

    # Specify use flags before completing bootstrap
    tee ${ccr_compat}/etc/portage/package.use <<EOF
# make sure that gold linker is installed with binutils
sys-devel/binutils gold
EOF

    # Continue gentoo prefix bootstrap and complete installation
    USE_CPU_CORES=$num_procs /tmp/bootstrap-prefix.sh $ccr_compat noninteractive

    # Check to ensure gentoo prefix was installed correctly
    if [[ ! -f "${ccr_compat}/startprefix" ]]; then
        fatal_error "Failed to find startprefix shell script. Something went wrong!"
    fi
}

function setup_locale() {
    local ccr_compat="$1"
    tee ${ccr_compat}/etc/locale.gen <<EOF
en_US.UTF-8 UTF-8
EOF

    $ccr_compat/usr/sbin/locale-gen

    tee ${ccr_compat}/etc/env.d/02locale <<EOF
# Configuration file for eselect
# This file has been automatically generated.
LANG="en_US.utf8"
EOF
}

function setup_overlay() {
    local ccr_compat="$1"

    # Install required packages
     emerge gentoolkit dev-vcs/git app-eselect/eselect-repository

    # Setup ubccr overlay
    cd ${ccr_compat}/var/db/repos
    git clone https://github.com/ubccr/gentoo-overlay.git ubccr

    mkdir -p ${ccr_compat}/etc/portage/repos.conf

    tee ${ccr_compat}/etc/portage/repos.conf/ubccr.conf <<EOF
[ubccr]
location = ${ccr_compat}/var/db/repos/ubccr
sync-type = git
sync-uri = https://github.com/ubccr/gentoo-overlay.git
masters = gentoo
priority = 50
auto-sync = yes
EOF

    tee ${ccr_compat}/etc/portage/repos.conf/gentoo.conf <<EOF
[gentoo]
sync-type = webrsync
auto-sync = no
EOF

    # Configure portage
    cd ${ccr_compat}/etc/portage
    ln -f -s ${ccr_compat}/var/db/repos/ubccr/etc/portage/package.* .
    ln -s ${ccr_compat}/var/db/repos/ubccr/etc/portage/sets .
    ln -s ${ccr_compat}/var/db/repos/ubccr/etc/portage/env .
}

function install_packages() {
    # Install custom package set
    emerge --update --newuse --deep --complete-graph --verbose @ubccr-${CCR_VERSION}-linux-x86_64
}

if [[ -z "$CCR_VERSION" ]]; then
    fatal_error "Missing CCR_VERSION env variable."
fi

# Check if the CCR_VERSION number is valid, i.e. matches the format YYYY.DD
if ! echo "${CCR_VERSION}" | egrep -q '^20[0-9][0-9]\.(0[0-9]|1[0-2])$'
then
    fatal_error "${CCR_VERSION} is not a valid CCR version."
fi

ccr_compat="/cvmfs/soft.ccr.buffalo.edu/versions/${CCR_VERSION}/compat"

install_prefix $ccr_compat
. $ccr_compat/etc/profile
setup_locale $ccr_compat
setup_overlay $ccr_compat
install_packages
