# Add host specific software (/opt/software/bin) and Slurm to $PATH
for d in /opt/software/slurm/bin /opt/software/bin /opt/slurm/bin ; do
    if [[ -d "$d" ]]; then
        export PATH=$d:$PATH
    fi
done
