# Set custom prompt
# export PS1="(CCRv${CCR_VERSION}) [\u@\h:\w]$ "

# aarch64 (Arm 64-bit), ppc64le (POWER 64-bit), x86_64 (x86 64-bit)
export CCR_CPU_FAMILY=$(uname -m)

# set $EPREFIX since that is basically a standard in Gentoo Prefix
export EPREFIX=$CCR_PREFIX/compat

if [[ -z "$CCR_CLUSTER" && -r /etc/environment ]]; then
   # try to recover from /etc/environment (not used by slurm)
   export CCR_CLUSTER=$(grep ^CCR_CLUSTER /etc/environment | cut -d= -f2)
fi

if [[ -z "$CCR_CLUSTER" ]]; then
   export CCR_CLUSTER="ub-hpc"
fi

# TODO: support more os types? 
export CCR_OS_TYPE='linux'
if [[ $(uname -s) == 'Linux' ]]; then
    export CCR_OS_TYPE='linux'
fi

if [ -d $EPREFIX ]; then
   export CCR_ARCH=$($EPREFIX/usr/bin/python3 ${CCR_INIT_DIR}/profile/ccr-arch.py) 
fi

# Do we want to set the umask here? 
# umask 0027
