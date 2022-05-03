#!/bin/bash

# Fetch and ingest pending development software builds from CCR mirrors repo.

ccr_mirrors="http://mirrors.ccr.buffalo.edu/ccr/software-dev/"
script_dir=$(dirname "$(readlink -f "$BASH_SOURCE")")
ingest_script="${script_dir}/ingest-tarball.sh"

tmpdir=`mktemp -d`

echo ">> Fetching latest dev packages"
wget -q -r -l1 -nH -np --cut-dirs 2 "${ccr_mirrors}" -P "${tmpdir}" -A 'ccr*.tar.gz'

for f in ${tmpdir}/*.tar.gz; do
    $ingest_script $f
done

echo ">> Cleaning up tmpdir"
rm -r ${tmpdir}
