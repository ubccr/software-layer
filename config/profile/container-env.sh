# CCR container custom shell prompt
export PS1="(v${CCR_VERSION}) \[\033[01;32m\]\u@\h\[\033[01;34m\] \w \$\[\033[00m\] "

confdir=$(/usr/bin/dirname "$(/usr/bin/readlink -f "$BASH_SOURCE")")
source $confdir/bash.sh
