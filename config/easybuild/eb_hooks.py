# Hooks to customize how EasyBuild installs software in CCR
# see https://docs.easybuild.io/en/latest/Hooks.html
import os
import hashlib

from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.config import build_option, update_build_option
from easybuild.tools.systemtools import get_cpu_architecture
from easybuild.tools.environment import setvar

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

MATLAB_MODLUAFOOTER = """

require("SitePackage")
local found = find_and_define_license_file("MLM_LICENSE_FILE","matlab")
if (not found) then
        local error_message = [[
        We did not find a suitable license for Matlab. If you have access to one, you can create the file $HOME/.licenses/matlab.lic with the license information. If you think you should have access to one, please write to ccr-help@buffalo.edu.
        ]]
        LmodError(error_message)
end
setenv("MATLAB_LOG_DIR","/tmp")
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

    if name == 'matlab':
        ec['modluafooter'] += (MATLAB_MODLUAFOOTER)

    if moduleclass == 'compiler' and not name == 'gcccore' and not name == 'llvm':
        if name in ['iccifort', 'intel-compilers']:
            name = 'intel'
        comp = os.path.join('Compiler', name + ec['version'][:ec['version'].find('.')])
        ec['modluafooter'] += COMPILER_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, sub_path=comp)
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

    # Intel needs to know where to find the license
    if ec.name in ('iccifort', 'iimpi', 'imkl', 'impi', 'intel-compilers'):
        setvar("LM_LICENSE_FILE", "28518@srv-m14-36.cbls.ccr.buffalo.edu")

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

def cuda_config_opts(ec, prefix):
    """Inject configure options for cuda."""
    if ec.name == 'CUDA':
        ec.update('builddependencies', [('GCCcore', '11.2.0')])
        print_msg("Using custom build deps for %s: %s", ec.name, ec['builddependencies'])
    else:
        raise EasyBuildError("cuda-specific hook triggered for non-cuda easyconfig?!")

def matlab_config_opts(ec, prefix):
    """Custom config options for MATLAB."""
    if ec.name != 'MATLAB':
        raise EasyBuildError("matlab-specific hook triggered for non-matlab easyconfig?!")

    print_msg(f"Checking for R{ec.version}_Linux.iso in current directory..")
    try:
        sha256_hash = hashlib.sha256()
        with open(f"R{ec.version}_Linux.iso", "rb") as f:
            print_msg("Found R%s_Linux.iso computing sha256 checksum..", ec.version)
            for byte_block in iter(lambda: f.read(4096),b""):
                sha256_hash.update(byte_block)
            sha256sum = sha256_hash.hexdigest()
            print_msg("Done. updating checksums with: %s", sha256sum)
            ec['checksums'] = [sha256sum]
    except FileNotFoundError:
        raise EasyBuildError(f"Failed to find R{ec.version}_Linux.iso please download from Mathworks")

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

def vtk_eprefix(ec, eprefix):
    """Fix VTK missing pthread library linking via added configuration options."""
    if ec.name == 'VTK':
        ec.update('configopts', '--with-sysroot=%s' % eprefix)
        ec.update('configopts', '-DVTK_REQUIRED_SHARED_LINKER_FLAGS=-lpthread')
        print_msg("Using custom configure option for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("VTK-specific hook for libpthread triggered for non-VTK easyconfig?!")

def pre_configure_hook(self, *args, **kwargs):
    """Main pre-configure hook: trigger custom functions based on software name."""
    if self.name in PRE_CONFIGURE_HOOKS:
        PRE_CONFIGURE_HOOKS[self.name](self, *args, **kwargs)

def pre_postproc_hook(self, *args, **kwargs):
    """Main pre-postproc hook: trigger custom functions based on software name."""
    if self.name in PRE_POSTPROC_HOOKS:
        PRE_POSTPROC_HOOKS[self.name](self, *args, **kwargs)

def iccifort_postproc(ec, *args, **kwargs):
    """Add post install cmds for iccifort. These were Adopted from ComputeCanada
       https://github.com/ComputeCanada/easybuild-computecanada-config/blob/main/cc_hooks_gentoo.py"""

    if ec.name == 'iccifort':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icc.cfg',
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compilers_and_libraries_%(version)s/linux/bin/intel64/icpc.cfg',
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s",
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/compilers_and_libraries_%(version)s/linux/compiler/lib --add_origin",
            "patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' %(installdir)s/compilers_and_libraries_%(version)s/linux/lib/LLVMgold.so",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("iccifort-specific hook triggered for non-iccifort easyconfig?!")

def intel_postproc(ec, *args, **kwargs):
    """Add post install cmds for intel-compilers. These were Adopted from ComputeCanada
       https://github.com/ComputeCanada/easybuild-computecanada-config/blob/main/cc_hooks_gentoo.py"""

    if ec.name == 'intel':
        ec.cfg['postinstallcmds'] = [
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/intel64/icc.cfg',
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/intel64/icpc.cfg',
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/intel64/ifort.cfg',
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/ifx.cfg',
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/icx.cfg',
            'echo "-Xlinker -rpath=${LIBRARY_PATH}:${EBROOTGCCCORE}/lib64" >> ${EBROOTINTELMINCOMPILERS}/compiler/${EBVERSIONINTELMINCOMPILERS}/linux/bin/icpx.cfg',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    elif ec.name == 'intel-compilers':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/icc.cfg',
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/icpc.cfg',
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compiler/%(version)s/linux/bin/icx.cfg',
            'echo "-isystem ${EPREFIX}/usr/include" > %(installdir)s/compiler/%(version)s/linux/bin/icpx.cfg',
            'echo "-L$EBROOTGCCCORE/lib64" >> %(installdir)s/compiler/%(version)s/linux/bin/icx.cfg',
            'echo "-L$EBROOTGCCCORE/lib64" >> %(installdir)s/compiler/%(version)s/linux/bin/icpx.cfg',
            'echo "-Wl,-dynamic-linker $EPREFIX/lib64/ld-linux-x86-64.so.2" >> %(installdir)s/compiler/%(version)s/linux/bin/icx.cfg',
            'echo "-Wl,-dynamic-linker $EPREFIX/lib64/ld-linux-x86-64.so.2" >> %(installdir)s/compiler/%(version)s/linux/bin/icpx.cfg',
            'echo "#!$EPREFIX/bin/sh" > %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp',
            'echo "exec %(installdir)s/compiler/%(version)s/linux/bin/dpcpp --sysroot=$EPREFIX -Wl,-dynamic-linker $EPREFIX/lib64/ld-linux-x86-64.so.2 -L$EBROOTGCCCORE/lib64 \${1+\\"\$@\\"}" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp',
            'chmod +x %(installdir)s/compiler/%(version)s/linux/bin/intel64/dpcpp',
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/compiler/%(version)s/linux/bin --add_origin --add_path=%(installdir)s/compiler/%(version)s/linux/compiler/lib/intel64_lin",
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s",
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/compiler/%(version)s/linux/compiler/lib --add_origin",
            "patchelf --set-rpath '$ORIGIN/../lib:$ORIGIN/../compiler/lib/intel64' %(installdir)s/compiler/%(version)s/linux/lib/icx-lto.so",
            "patchelf --set-rpath '$ORIGIN:$ORIGIN/../../../../../tbb/latest/lib/intel64/gcc4.8' %(installdir)s/compiler/%(version)s/linux/lib/x64/libintelocl.so",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("intel-specific hook triggered for non-intel easyconfig?!")

def impi_postproc(ec, *args, **kwargs):
    """Add post install cmds for impi. These were Adopted from ComputeCanada
       https://github.com/ComputeCanada/easybuild-computecanada-config/blob/main/cc_hooks_gentoo.py"""

    if ec.name == 'impi':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        # Paths differ between versions of intel
        version_major = ec.version.split('.')[0]
        if version_major == '2019':
            ec.cfg['postinstallcmds'] = [
                # Fix mpirun from IntelMPI to explicitly unset I_MPI_PMI_LIBRARY. it can only be used with srun.
                "sed -i 's@\\(#!/bin/sh.*\\)$@\\1\\nunset I_MPI_PMI_LIBRARY@' %(installdir)s/intel64/bin/mpirun",
                f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/intel64/bin --add_path='$ORIGIN/../lib/release'",
                f"for dir in release release_mt debug debug_mt; do {ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/intel64/lib/$dir --add_path='$ORIGIN/../../libfabric/lib'; done",
                "patchelf --set-rpath $EBROOTUCX/lib --force-rpath %(installdir)s/intel64/libfabric/lib/prov/libmlx-fi.so",
            ]
        elif version_major == '2021':
            ec.cfg['postinstallcmds'] = [
                # Fix mpirun from IntelMPI to explicitly unset I_MPI_PMI_LIBRARY. it can only be used with srun.
                "sed -i 's@\\(#!/bin/sh.*\\)$@\\1\\nunset I_MPI_PMI_LIBRARY@' %(installdir)s/mpi/%(version)s/bin/mpirun",
                f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/mpi/%(version)s/bin --add_path='$ORIGIN/../lib/release'",
                f"for dir in release release_mt debug debug_mt; do {ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/mpi/%(version)s/lib/$dir --add_path='$ORIGIN/../../libfabric/lib'; done",
                "patchelf --set-rpath $EBROOTUCX/lib --force-rpath %(installdir)s/mpi/%(version)s/libfabric/lib/prov/libmlx-fi.so",
            ]

        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("impi-specific hook triggered for non-impi easyconfig?!")

def imkl_postproc(ec, *args, **kwargs):
    """Add post install cmds for imkl."""

    if ec.name == 'imkl':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s",
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/compiler/%(version)s/linux/compiler/lib --add_origin",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("imkl-specific hook triggered for non-imkl easyconfig?!")

def matlab_postproc(ec, *args, **kwargs):
    """Add post install cmds for matlab."""

    if ec.name == 'MATLAB':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            'chmod -R u+w %(installdir)s',
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("matlab-specific hook triggered for non-matlab easyconfig?!")

def cuda_postproc(ec, *args, **kwargs):
    """Add post install cmds for cuda."""

    if ec.name == 'CUDA':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("cuda-specific hook triggered for non-cuda easyconfig?!")

def nvhpc_postproc(ec, *args, **kwargs):
    """Add post install cmds for nvhpc."""

    if ec.name == 'NVHPC':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/Linux_x86_64/%(version)s",
            f'echo "set DEFLIBDIR=$EPREFIX/lib;" >> %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
            f'echo "set DEFSTDOBJDIR=$EPREFIX/lib;" >> %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
            #f'echo "set NORPATH=YES;" >> %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("nvhpc-specific hook triggered for non-nvhpc easyconfig?!")

PARSE_HOOKS = {
    'fontconfig': fontconfig_add_fonts,
    'UCX': ucx_eprefix,
    'VTK': vtk_eprefix,
    'OpenMPI': openmpi_config_opts,
    'OpenBLAS': openblas_config_opts,
    'PMIx': pmix_config_opts,
    'CUDA': cuda_config_opts,
    'MATLAB': matlab_config_opts,
}

PRE_CONFIGURE_HOOKS = {
}

PRE_POSTPROC_HOOKS = {
    'iccifort': iccifort_postproc,
    'impi': impi_postproc,
    'imkl': imkl_postproc,
    'intel-compilers': intel_postproc,
    'intel': intel_postproc,
    'MATLAB': matlab_postproc,
    'CUDA': cuda_postproc,
    'NVHPC': nvhpc_postproc,
}
