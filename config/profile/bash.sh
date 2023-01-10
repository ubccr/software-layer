CCR_CVMFS_REPO="/cvmfs/soft.ccr.buffalo.edu"
CCR_VERSION="2023.01"
CCR_INIT_DIR=$(dirname "$(dirname "$(readlink -f "$BASH_SOURCE")")")

# Allow users to override CCR_VERSION
if [ -f ${HOME}/.ccr/version ]; then
    read -r ccrver<${HOME}/.ccr/version

    if echo "${ccrver}" | egrep -q '^20[0-9][0-9]\.(0[0-9]|1[0-2])$'; then
        if [ -d $CCR_CVMFS_REPO/versions/$ccrver ]; then
	        CCR_VERSION="${ccrver}"
	        CCR_INIT_DIR="${CCR_CVMFS_REPO}/versions/${ccrver}/config"
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
export CCR_VERSION
export CCR_CVMFS_REPO
export CCR_PREFIX=$CCR_CVMFS_REPO/versions/$CCR_VERSION
export CCR_EASYBUILD_PATH=$CCR_PREFIX/easybuild
export CCR_BANALBUILD_PATH=$CCR_PREFIX/banalbuild

if [[ $UID -ge 1000 ]]; then
    for file in ${CCR_INIT_DIR}/profile/profile.d/*.sh; do
        if [[ -r "$file" ]]; then
            source $file
        fi
    done
fi
