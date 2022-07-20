# Add host specific software to $PATH
for d in /opt/software/slurm/bin /opt/software/nvidia/bin /opt/software/bin ; do
    if [[ -d "$d" ]]; then
        export PATH=$d:$PATH
    fi
done
