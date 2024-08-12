# CCR container custom shell prompt
export PS1="(v${CCR_VERSION}) \[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] "

if [ -d "/opt/software/nvidia" ]; then
    export LD_LIBRARY_PATH=/.singularity.d/libs
fi

confdir=$(/usr/bin/dirname "$(/usr/bin/readlink -f "$BASH_SOURCE")")
source $confdir/bash.sh
