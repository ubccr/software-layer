CCR_CVMFS_REPO="/cvmfs/soft.ccr.buffalo.edu"
CCR_COMPAT_VERSION="2023.01"
CCR_INIT_DIR=$(dirname "$(dirname "$(readlink -f "$BASH_SOURCE")")")

if [[ -z $FORCE_CCR_INIT ]]; then
    FORCE_CCR_INIT=0
fi
if [[ -z $FORCE_CCR_LEGACY ]]; then
    FORCE_CCR_LEGACY=0
fi
if [[ -f $HOME/.force_ccr_init ]]; then
    FORCE_CCR_INIT=1
fi
if [[ -f $HOME/.force_ccr_legacy ]]; then
    FORCE_CCR_LEGACY=1
fi

# XXX remove me soon. Migrate to use ~/.modulerc
if [[ $UID -ge 1000 && -f ${HOME}/.ccr_new_modules ]]; then
    rm ${HOME}/.ccr_new_modules
    if [[ ! -f ${HOME}/.modulerc ]]; then
        echo "module-version ccrsoft/2023.01 default" > $HOME/.modulerc
    elif ! grep --quiet ccrsoft $HOME/.modulerc; then
        echo "module-version ccrsoft/2023.01 default" >> $HOME/.modulerc
    fi
fi

# Allow users to override CCR_COMPAT_VERSION
if [ -f ${HOME}/.ccr/compat ]; then
    read -r ccrver<${HOME}/.ccr/compat

    if echo "${ccrver}" | egrep -q '^20[0-9][0-9]\.(0[0-9]|1[0-2])$'; then
        if [ -d $CCR_CVMFS_REPO/compat/gentoo/$ccrver ]; then
            CCR_COMPAT_VERSION="${ccrver}"
        fi
    fi
fi

# Slurp in any custom easybuild paths
if [ -f ${HOME}/.ccr/modulepaths ]; then
    read -r mpaths<${HOME}/.ccr/modulepaths
    export CCR_CUSTOM_BUILD_PATHS="${mpaths}"
fi

# Defines base CCR environment variables. These will be used by everything
export CCR_INIT_DIR
export CCR_COMPAT_VERSION
export CCR_CVMFS_REPO
export CCR_COMPAT_PREFIX=$CCR_CVMFS_REPO/compat/gentoo/$CCR_COMPAT_VERSION

if [[ ($UID -ge 1000 && $FORCE_CCR_LEGACY -ne 1) || ($FORCE_CCR_INIT -eq 1) ]]; then
    for file in ${CCR_INIT_DIR}/profile/profile.d/*.sh; do
        if [[ -r "$file" ]]; then
            source $file
        fi
    done
elif [[ $UID -ge 1000 && $FORCE_CCR_LEGACY -eq 1 ]]; then
    distro=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')
    export GLOBAL_SCRATCH="/panasas/scratch"
    export LOCAL_SCRATCH="/scratch"
    export UTIL="/util"
    source /util/software/${distro}/lmod/lmod/init/profile
    export PATH="/opt/software/slurm/bin:$PATH"
fi
