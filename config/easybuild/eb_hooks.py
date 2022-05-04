# Hooks to customize how EasyBuild installs software in CCR
# see https://docs.easybuild.io/en/latest/Hooks.html
import os

from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.config import build_option, update_build_option
from easybuild.tools.systemtools import get_cpu_architecture

CCR_RPATH_OVERRIDE_ATTR = 'orig_rpath_override_dirs'

COMPILER_MODLUAFOOTER = """
prepend_path("MODULEPATH", pathJoin("{software_path}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/{ccr_version}/easybuild/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
end
add_property("type_","tools")
"""

MPI_MODLUAFOOTER = """

add_property("type_","mpi")
family("mpi")
"""

def get_ccr_envvar(ccr_envvar):
    """Get an CCR environment variable from the environment"""

    ccr_envvar_value = os.getenv(ccr_envvar)
    if ccr_envvar_value is None:
        raise EasyBuildError("$%s is not defined!", ccr_envvar)

    return ccr_envvar_value

def set_modluafooter(ec):
    software_path = get_ccr_envvar('CCR_SOFTWARE_PATH')
    ccr_version = get_ccr_envvar('CCR_VERSION')
    moduleclass = ec.get('moduleclass','')
    name = ec['name'].lower()

    if name == 'openmpi':
        ec['modluafooter'] += (MPI_MODLUAFOOTER)

    if moduleclass == 'compiler' and not name == 'gcccore' and not name == 'llvm':
        if name in ['iccifort', 'intel-compilers']:
            name = 'intel'
        comp = os.path.join('Compiler', name + ec['version'][:ec['version'].find('.')])
        ec['modluafooter'] += (COMPILER_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, sub_path=comp) + 'family("compiler")\n')
    if ec['name'] == 'CUDAcore':
        comp = os.path.join('CUDA', 'cuda' + '.'.join(ec['version'].split('.')[:2]))
        ec['modluafooter'] += COMPILER_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, sub_path=comp)

def pre_module_hook(self, *args, **kwargs):
    "Modify module footer (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    set_modluafooter(self.cfg)
    self.cfg.enable_templating = orig_enable_templating

def get_rpath_override_dirs(software_name):
    # determine path to installations in software layer via $CCR_SOFTWARE_PATH
    ccr_software_path = get_ccr_envvar('CCR_SOFTWARE_PATH')
    ccr_version = get_ccr_envvar('CCR_VERSION')

    # construct the rpath override directory stub
    rpath_injection_stub = os.path.join(
        # Make sure we are looking inside the `host_injections` directory
        ccr_software_path.replace(ccr_version, os.path.join('host_injections', ccr_version), 1),
        # Add the subdirectory for the specific software
        'rpath_overrides',
        software_name,
        # We can't know the version, but this allows the use of a symlink
        # to facilitate version upgrades without removing files
        'system',
    )

    # Allow for libraries in lib or lib64
    rpath_injection_dirs = [os.path.join(rpath_injection_stub, x) for x in ('lib', 'lib64')]

    return rpath_injection_dirs


def parse_hook(ec, *args, **kwargs):
    """Main parse hook: trigger custom functions based on software name."""

    # determine path to Prefix installation in compat layer via $EPREFIX
    eprefix = get_ccr_envvar('EPREFIX')

    if ec.name in PARSE_HOOKS:
        PARSE_HOOKS[ec.name](ec, eprefix)


def pre_prepare_hook(self, *args, **kwargs):
    """Main pre-prepare hook: trigger custom functions."""

    # Check if we have an MPI family in the toolchain (returns None if there is not)
    mpi_family = self.toolchain.mpi_family()

    # Inject an RPATH override for MPI (if needed)
    if mpi_family:
        # Get list of override directories
        mpi_rpath_override_dirs = get_rpath_override_dirs(mpi_family)

        # update the relevant option (but keep the original value so we can reset it later)
        if hasattr(self, CCR_RPATH_OVERRIDE_ATTR):
            raise EasyBuildError("'self' already has attribute %s! Can't use pre_prepare hook.",
                                 CCR_RPATH_OVERRIDE_ATTR)

        setattr(self, CCR_RPATH_OVERRIDE_ATTR, build_option('rpath_override_dirs'))
        if getattr(self, CCR_RPATH_OVERRIDE_ATTR):
            # self.CCR_RPATH_OVERRIDE_ATTR is (already) a colon separated string, let's make it a list
            orig_rpath_override_dirs = [getattr(self, CCR_RPATH_OVERRIDE_ATTR)]
            rpath_override_dirs = ':'.join(orig_rpath_override_dirs + mpi_rpath_override_dirs)
        else:
            rpath_override_dirs = ':'.join(mpi_rpath_override_dirs)
        update_build_option('rpath_override_dirs', rpath_override_dirs)
        print_msg("Updated rpath_override_dirs (to allow overriding MPI family %s): %s",
                  mpi_family, rpath_override_dirs)


def post_prepare_hook(self, *args, **kwargs):
    """Main post-prepare hook: trigger custom functions."""

    if hasattr(self, CCR_RPATH_OVERRIDE_ATTR):
        # Reset the value of 'rpath_override_dirs' now that we are finished with it
        update_build_option('rpath_override_dirs', getattr(self, CCR_RPATH_OVERRIDE_ATTR))
        print_msg("Resetting rpath_override_dirs to original value: %s", getattr(self, CCR_RPATH_OVERRIDE_ATTR))
        delattr(self, CCR_RPATH_OVERRIDE_ATTR)


def fontconfig_add_fonts(ec, eprefix):
    """Inject --with-add-fonts configure option for fontconfig."""
    if ec.name == 'fontconfig':
        # make fontconfig aware of fonts included with compat layer
        with_add_fonts = '--with-add-fonts=%s' % os.path.join(eprefix, 'usr', 'share', 'fonts')
        ec.update('configopts', with_add_fonts)
        print_msg("Added '%s' configure option for %s", with_add_fonts, ec.name)
    else:
        raise EasyBuildError("fontconfig-specific hook triggered for non-fontconfig easyconfig?!")


def openmpi_config_opts(ec, prefix):
    """Inject configure options for openmpi."""
    if ec.name == 'OpenMPI':
        opts = '--with-slurm --with-pmi=/opt/software/slurm --with-hwloc=external '
        ec.update('configopts', opts)
        print_msg("Added '%s' configure option for %s", opts, ec.name)
    else:
        raise EasyBuildError("openmpi-specific hook triggered for non-openpmi easyconfig?!")

def pmix_config_opts(ec, eprefix):
    """Inject configure options for pmix."""
    if ec.name == 'PMIx':
        ec.update('configopts', '--with-sysroot=%s' % eprefix)
        ec.update('configopts', '--with-hwloc=%s' % os.path.join(eprefix, 'usr'))
        ec.update('configopts', '--with-zlib=%s' % os.path.join(eprefix, 'usr'))
        print_msg("Using custom configure option for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("pmix-specific hook triggered for non-pmix easyconfig?!")

def openblas_config_opts(ec, prefix):
    """Inject configure options for openblas."""
    if ec.name == 'OpenBLAS':
        opts = {'sse3': 'DYNAMIC_ARCH=1',
                'avx': 'TARGET=SANDYBRIDGE',
                'avx2': 'DYNAMIC_ARCH=1 DYNAMIC_LIST="HASWELL ZEN SKYLAKEX"',
                'avx512': 'TARGET=SKYLAKEX'}[os.getenv('CCR_ARCH')] + ' NUM_THREADS=64'
        ec.update('buildopts', opts)
        ec.update('installopts', opts)
        ec.update('testopts', opts)
        print_msg("Added '%s' configure/build/install options for %s", opts, ec.name)
    else:
        raise EasyBuildError("openblas-specific hook triggered for non-openblas easyconfig?!")

def ucx_eprefix(ec, eprefix):
    """Make UCX aware of compatibility layer via additional configuration options."""
    if ec.name == 'UCX':
        ec.update('configopts', '--with-sysroot=%s' % eprefix)
        ec.update('configopts', '--with-rdmacm=%s' % os.path.join(eprefix, 'usr'))
        ec.update('configopts', '--with-verbs=%s' % os.path.join(eprefix, 'usr'))
        ec.update('configopts', {'sse3': '--without-avx --without-sse41 --without-sse42 '}.get(os.getenv('CCR_ARCH'), ''))
        print_msg("Using custom configure option for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("UCX-specific hook triggered for non-UCX easyconfig?!")


def pre_configure_hook(self, *args, **kwargs):
    """Main pre-configure hook: trigger custom functions based on software name."""
    if self.name in PRE_CONFIGURE_HOOKS:
        PRE_CONFIGURE_HOOKS[self.name](self, *args, **kwargs)

PARSE_HOOKS = {
    'fontconfig': fontconfig_add_fonts,
    'UCX': ucx_eprefix,
    'OpenMPI': openmpi_config_opts,
    'OpenBLAS': openblas_config_opts,
    'PMIx': pmix_config_opts,
}

PRE_CONFIGURE_HOOKS = {
}
