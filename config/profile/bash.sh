export CCR_INIT_DIR=$(dirname "$(dirname "$(readlink -f "$BASH_SOURCE")")")

if [[ -z $FORCE_CCR_INIT ]]; then
    FORCE_CCR_INIT=0
fi
if [[ -f $HOME/.force_ccr_init ]]; then
    FORCE_CCR_INIT=1
fi

if [[ $UID -ge 1000 || $FORCE_CCR_INIT -eq 1 ]]; then
    for file in ${CCR_INIT_DIR}/profile/profile.d/*.sh; do
        if [[ -r "$file" ]]; then
            source $file
        fi
    done
fi
