CCR_INIT_DIR=$(dirname "$(dirname "$(readlink -f "$BASH_SOURCE")")")

export CCR_INIT_DIR

for file in ${CCR_INIT_DIR}/profile/profile.d/*.sh; do
if [[ -r "$file" ]]; then
    source $file
fi
done
