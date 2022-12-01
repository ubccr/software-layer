# Initialization script to configure EasyBuild. This script is meant to be
# sourced and assumed you've already sourced CCR's bash environment scripts.
#
# EasyBuild can be configured via environment variables or configuration files.
# We use both, see config.cfg for additional settings. The reason for using
# both environment variables (in this file) and config settings (in config.cfg)
# is that sometimes we want to configure easybuild dynamically based on certain
# logic. We can do this easily in this bash script. For other settings that are
# more static we can just set them in config.cfg. 
#
# For deatiled docs on configuring EasyBuild see:
# https://docs.easybuild.io/en/latest/Configuration.html#available-configuration-settings

# First create a temporary work directory for all easybuilds.
# here we honor $TMPDIR if it is already defined, use /tmp otherwise
if [ -z $TMPDIR ]; then
    export WORKDIR=/tmp/$USER
else
    export WORKDIR=$TMPDIR/$USER
fi

TMPDIR=$(mktemp -d)

# avoid that pyc files for EasyBuild are stored in EasyBuild installation directory
export PYTHONPYCACHEPREFIX=$TMPDIR/pycache

# Path to our custom EasyBuild config settings file
export EASYBUILD_CONFIGFILES=${CCR_INIT_DIR}/easybuild/config.cfg

# Set custom Hierarchical module naming scheme. For details see here:
# https://easybuilders.github.io/easybuild-tutorial/2021-lust/module_naming_schemes/
# https://easybuild.io/files/hust14_paper.pdf
export EASYBUILD_INCLUDE_MODULE_NAMING_SCHEMES=${CCR_INIT_DIR}/easybuild/CCRHierarchicalMNS.py
export EASYBUILD_MODULE_NAMING_SCHEME=CCRHierarchicalMNS

export EASYBUILD_ALLOW_LOADED_MODULES=StdEnv,gentoo,easybuild
export EASYBUILD_PREFIX=${WORKDIR}/easybuild
export EASYBUILD_INSTALLPATH=${CCR_EASYBUILD_PATH}
export EASYBUILD_SUFFIX_MODULES_PATH=""
export EASYBUILD_SOURCEPATH=${WORKDIR}/easybuild/sources:${CCR_SOURCEPATH}

# just ignore OS dependencies for now, see https://github.com/easybuilders/easybuild-framework/issues/3430
export EASYBUILD_IGNORE_OSDEPS=1

export EASYBUILD_SYSROOT=${EPREFIX}

export EASYBUILD_DEBUG=1
export EASYBUILD_TRACE=1
export EASYBUILD_ZIP_LOGS=bzip2

export EASYBUILD_RPATH=1

export EASYBUILD_HOOKS=${CCR_INIT_DIR}/easybuild/eb_hooks.py

export EASYBUILD_MODULE_EXTENSIONS=1

# Here we set compiler optimization flags based on supported CCR_ARCH types
# See: https://docs.easybuild.io/en/latest/Controlling_compiler_optimization_flags.html
if [ "$CCR_ARCH" == avx2 ]; then
    export EASYBUILD_OPTARCH='NVHPC:tp=haswell;Intel:march=core-avx2 -axCore-AVX512;GCC:march=core-avx2'
elif [ "$CCR_ARCH" == avx512 ]; then
    export EASYBUILD_OPTARCH='NVHPC:tp=skylake;Intel:xCore-AVX512;GCC:march=skylake-avx512'
elif [ "$CCR_ARCH" == avx ]; then
    export EASYBUILD_OPTARCH='NVHPC:tp=sandybridge;Intel:xAVX;GCC:march=corei7-avx'
elif [ "$CCR_ARCH" == sse3 ]; then
    export EASYBUILD_OPTARCH='NVHPC:tp=px;Intel:msse3;GCC:march=nocona -mtune=generic'
else
    echo -e "\e[31mERROR: please set CCR_ARCH to sse3, avx, or avx2\e[0m" >&2
    exit 1
fi
