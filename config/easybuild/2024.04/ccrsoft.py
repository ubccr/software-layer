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
    'Python': ('3.11.5', [('GCCcore', '13.2.0')], None),
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
        'configopts': ('--with-slurm --with-pmi=/opt/software/slurm --with-hwloc=external ', Op.PREPEND),
    },
    'UCX': {
        'configopts': ('--with-rdmacm=$EPREFIX/usr --with-verbs=$EPREFIX/usr ', Op.PREPEND),
    },
    'SciPy-bundle': {
        'testopts': ({'neoverse-v2': "|| echo ignoring failing tests"}.get(os.getenv('CCR_ARCH'), ''), Op.REPLACE),
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
