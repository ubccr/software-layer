import os
import sys
from easybuild.easyblocks.generic.configuremake import obtain_config_guess
from easybuild.tools.run import run_cmd
from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.filetools import apply_regex_substitutions, copy_file, which

libdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if libdir not in sys.path:
    sys.path.append(libdir)

from ccr_hooks_common import Op

def gcc_postprepare(self, *args, **kwargs):
    """
    Post-configure hook for GCCcore:
    - copy RPATH wrapper script for linker commands to also have a wrapper in place with system type prefix like 'x86_64-pc-linux-gnu'
    """
    config_guess = obtain_config_guess()
    system_type, _ = run_cmd(config_guess, log_all=True)
    cmd_prefix = '%s-' % system_type.strip()
    for cmd in ('ld', 'ld.gold', 'ld.bfd'):
        wrapper = which(cmd)
        self.log.info("Path to %s wrapper: %s" % (cmd, wrapper))
        wrapper_dir = os.path.dirname(wrapper)
        prefix_wrapper = os.path.join(wrapper_dir, cmd_prefix + cmd)
        copy_file(wrapper, prefix_wrapper)
        self.log.info("Path to %s wrapper with '%s' prefix: %s" % (cmd, cmd_prefix, which(prefix_wrapper)))

        # we need to tweak the copied wrapper script, so that:
        regex_subs = [
            # - CMD in the script is set to the command name without prefix, because EasyBuild's rpath_args.py
            #   script that is used by the wrapper script only checks for 'ld', 'ld.gold', etc.
            #   when checking whether or not to use -Wl
            ('^CMD=.*', 'CMD=%s' % cmd),
            # - the path to the correct actual binary is logged and called
            ('/%s ' % cmd, '/%s ' % (cmd_prefix + cmd)),
        ]
        apply_regex_substitutions(prefix_wrapper, regex_subs)

DEPS = {
    ('OpenSSL', '1.1', ''): ('3', [('system', 'system')]),
    'Catch2': ('2.13.9', [('GCCcore', '13.2.0')]),
    'Python': ('3.11.5', [('GCCcore', '13.2.0')], ''),
    'CMake': ('3.27.6', [('GCCcore', '13.2.0')]),
    'cURL': ('8.3.0', [('GCCcore', '13.2.0')]),
}

HOOKS = {
    'GCCcore': {
        'post_prepare_hook': gcc_postprepare,
    },
}

CHANGES = {
    'EasyBuild': {
        'modluafooter': ('prepend_path("PATH", pathJoin(os.getenv("CCR_INIT_DIR"), "easybuild/bin"))', Op.REPLACE),
    },
    'OpenMPI': {
        'builddependencies': ({'x86_64': [('opa-psm2', '12.0.1')]}.get(os.getenv('CCR_CPU_FAMILY'), []), Op.APPEND_LIST),
        'preconfigopts': ('LDFLAGS="-L/usr/lib/x86_64-linux-gnu/slurm" ', Op.APPEND),
        'configopts': ('--with-slurm --with-pmi=/opt/software/slurm --with-hwloc=external ', Op.PREPEND),
        # See: https://github.com/easybuilders/easybuild-easyconfigs/issues/20233
        'modluafooter': ('setenv("OMPI_MCA_btl", "^ofi")\nsetenv("OMPI_MCA_mtl", "^ofi")', Op.APPEND),
    },
    'UCX': {
        'configopts': ('--with-rdmacm=$EPREFIX/usr --with-verbs=$EPREFIX/usr ', Op.PREPEND),
    },
    'SciPy-bundle': {
        'testopts': ({'neoverse-v2': "|| echo ignoring failing tests"}.get(os.getenv('CCR_ARCH'), ''), Op.REPLACE),
    },
    'CUDA': {
        'postinstallcmds': (
            [
                'for dir in %(installdir)s/{bin,nvvm}; do $CCR_INIT_DIR/easybuild/setrpaths.sh --path $dir; done',
                'for dir in %(installdir)s/{c,e,g,nsight,t}*; do $CCR_INIT_DIR/easybuild/setrpaths.sh --path $dir --add_origin; done'
            ], Op.APPEND_LIST),
    },
    'impi': {
        'postinstallcmds': (
            [
                "sed -i 's@\\(#!/bin/sh.*\\)$@\\1\\nunset I_MPI_PMI_LIBRARY@' %(installdir)s/mpi/%(version)s/bin/mpirun",
                "$CCR_INIT_DIR/easybuild/setrpaths.sh --path %(installdir)s/mpi/%(version)s/bin",
                "for i in %(installdir)s/mpi/%(version)s/bin/I*; do patchelf --set-rpath '$ORIGIN/../lib/release' --force-rpath $i; done",
                "patchelf --set-rpath '$ORIGIN/../lib/release:$ORIGIN/../libfabric/lib' --force-rpath %(installdir)s/mpi/%(version)s/bin/impi_info",
                "for dir in release debug; do $CCR_INIT_DIR/easybuild/setrpaths.sh --path %(installdir)s/mpi/%(version)s/lib/$dir --add_path='$ORIGIN/../../libfabric/lib'; done",
                'patchelf --set-rpath "\$ORIGIN/..:$EBROOTUCX/lib" --force-rpath %(installdir)s/mpi/%(version)s/libfabric/lib/prov/libmlx-fi.so',
                "$CCR_INIT_DIR/easybuild/setrpaths.sh --path %(installdir)s/mpi/%(version)s/libfabric/bin --add_path='$ORIGIN/../lib'",
            ], Op.APPEND_LIST),
    },
    'intel-compilers': {
        'postinstallcmds': (
            ['''
    for compname in icc icpc ifort; do
       echo "--sysroot=$EPREFIX" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/$compname.cfg
    done
    for compname in icx icpx ifx; do
       echo "--sysroot=$EPREFIX" > %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
       echo "-L$EBROOTGCCCORE/lib64" >> %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
       echo "-Wl,-dynamic-linker=$EPREFIX/lib64/ld-linux-x86-64.so.2" >> %(installdir)s/compiler/%(version)s/linux/bin/$compname.cfg
    done
    echo "#!$EPREFIX/bin/sh" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    echo "exec %(installdir)s/compiler/%(version)s/linux/bin/dpcpp --sysroot=$EPREFIX -Wl,-dynamic-linker=$EPREFIX/lib64/ld-linux-x86-64.so.2 -L$EBROOTGCCCORE/lib64 \${1+\\"\$@\\"}" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    chmod +x %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp
    $CCR_INIT_DIR/easybuild/setrpaths.sh --path %(installdir)s
    $CCR_INIT_DIR/easybuild/setrpaths.sh --path %(installdir)s/compiler/%(version)s/linux/compiler/lib --add_origin
    for i in %(installdir)s/compiler/%(version)s/linux/lib/*.so; do
       patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' $i
    done
    patchelf --set-rpath '$ORIGIN:$ORIGIN/../../../../../tbb/%(version)s/lib/intel64/gcc4.8' %(installdir)s/compiler/%(version)s/linux/lib/x64/libintelocl.so
            '''], Op.APPEND_LIST),
    },
}


COMPILER_MODLUAFOOTER = """
prepend_path("MODULEPATH", pathJoin("{software_path}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
end

local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
if customBuildPaths ~= nil then
 for customPath in customBuildPaths:split(":") do
   if isDir(pathJoin(customPath, "{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
     prepend_path("MODULEPATH", pathJoin(customPath, "{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
   end
 end
end
add_property("type_","tools")
"""

MPI_MODLUAFOOTER = """
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
end

local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
if customBuildPaths ~= nil then
 for customPath in customBuildPaths:split(":") do
   if isDir(pathJoin(customPath, "{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
     prepend_path("MODULEPATH", pathJoin(customPath, "{ccr_version}/{cpu_family}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
   end
 end
end

add_property("type_","mpi")
family("mpi")
"""
