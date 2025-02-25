export CCR_CVMFS_REPO="/cvmfs/soft.ccr.buffalo.edu"

# aarch64 (Arm 64-bit), x86_64 (x86 64-bit)
export CCR_CPU_FAMILY=$(/usr/bin/uname -m)
export CCR_OS_TYPE='linux'

if [[ -z $CCR_COMPAT_VERSION ]]; then
    # Default version of compatibility layer used to run lmod
    CCR_COMPAT_VERSION="2023.01"
fi

# Allow users to override CCR_COMPAT_VERSION
if [ -f ${HOME}/.ccr/compat ]; then
    read -r ccrver<${HOME}/.ccr/compat

    if echo "${ccrver}" | egrep -q '^20[0-9][0-9]\.(0[0-9]|1[0-2])$'; then
        if [ -d $CCR_CVMFS_REPO/versions/$ccrver/compat/$CCR_OS_TYPE/$CCR_CPU_FAMILY ]; then
            CCR_COMPAT_VERSION="${ccrver}"
        fi
    fi
fi

if [ "$CCR_COMPAT_VERSION" = "2023.01" ]; then
    CCR_COMPAT_PREFIX=$CCR_CVMFS_REPO/versions/$CCR_COMPAT_VERSION/compat
else
    CCR_COMPAT_PREFIX=$CCR_CVMFS_REPO/versions/$CCR_COMPAT_VERSION/compat/$CCR_OS_TYPE/$CCR_CPU_FAMILY
fi

export EPREFIX=$CCR_COMPAT_PREFIX
export CCR_VERSION=$CCR_COMPAT_VERSION

if [ -d $EPREFIX ]; then
   # set micro-architecture
   export CCR_ARCH=$($EPREFIX/usr/bin/python3 ${CCR_INIT_DIR}/profile/ccr-arch.py)
fi

if [[ -z "$CCR_CLUSTER" && -r /etc/environment ]]; then
   # try to recover from /etc/environment (not used by slurm)
   export CCR_CLUSTER=$(grep ^CCR_CLUSTER /etc/environment | cut -d= -f2)
fi

if [[ -z "$CCR_CLUSTER" ]]; then
   export CCR_CLUSTER="ub-hpc"
fi

# Slurp in any custom easybuild paths
if [ -f ${HOME}/.ccr/modulepaths ]; then
    read -r mpaths<${HOME}/.ccr/modulepaths
    export CCR_CUSTOM_BUILD_PATHS="${mpaths}"
fi

# Set custom prompt
# export PS1="(CCRv${CCR_VERSION}) [\u@\h:\w]$ "

# Do we want to set the umask here? 
# umask 0027
