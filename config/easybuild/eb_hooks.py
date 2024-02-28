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
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
end

local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
if customBuildPaths ~= nil then
 for customPath in customBuildPaths:split(":") do
   if isDir(pathJoin(customPath, "{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
     prepend_path("MODULEPATH", pathJoin(customPath, "{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
   end
 end
end
add_property("type_","tools")
"""

CUSTOMEB_MODLUAFOOTER  = """

prepend_path("PATH", pathJoin(os.getenv("CCR_INIT_DIR"), "easybuild/bin"))
"""

ANACONDA_MODLUAFOOTER  = """

setenv("TERMINFO", pathJoin(os.getenv("EPREFIX"), "usr/share/terminfo"))
"""

MPI_MODLUAFOOTER = """
if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
    prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild/{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
end

local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
if customBuildPaths ~= nil then
 for customPath in customBuildPaths:split(":") do
   if isDir(pathJoin(customPath, "{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}")) then
     prepend_path("MODULEPATH", pathJoin(customPath, "{ccr_version}/modules", os.getenv("CCR_ARCH"), "{sub_path}"))
   end
 end
end

add_property("type_","mpi")
family("mpi")
"""

MATLAB_MODLUAFOOTER = """
prepend_path("PATH", "{eprefix}/usr/sbin")
prepend_path("PATH", "{eprefix}/usr/bin")
require("SitePackage")
local found = find_and_define_license_file("MLM_LICENSE_FILE","matlab")
if (not found) then
        local error_message = [[
        We did not find a suitable license for Matlab. If you have access to one, you can create the file $HOME/.licenses/matlab.lic with the license information. If you think you should have access to one, please write to ccr-help@buffalo.edu.
        ]]
        LmodError(error_message)
end
setenv("MATLAB_LOG_DIR","/tmp")
setenv("FONTCONFIG_PATH","{eprefix}/etc/fonts")
"""

GUROBI_MODLUAFOOTER = """
require("SitePackage")
local found = find_and_define_license_file("GRB_LICENSE_FILE","gurobi")
if (not found) then
        local error_message = [[
        We did not find a suitable license for Gurobi. If you have access to one, you can create the file $HOME/.licenses/gurobi.lic with the license information. If you think you should have access to one, please write to ccr-help@buffalo.edu.
        ]]
        LmodError(error_message)
end
"""

PAVILION_MODLUAFOOTER = """
if isDir(pathJoin(os.getenv("HOME"), "testsuite/sanitarium")) then
    setenv("PAV_CONFIG_DIR", pathJoin(os.getenv("HOME"), "testsuite/sanitarium"))
end
"""

ANSYS_MODLUAFOOTER = """
setenv("FONTCONFIG_PATH","{eprefix}/etc/fonts")
setenv("QT_XKB_CONFIG_ROOT","{ebrootx11}/share/X11/xkb")

require("SitePackage")
local found, path = find_and_define_license_file("__ANSYS_LICENSE_FILE", "ansys")
if (not found) then
	local error_message = [[
We did not find a suitable license for ANSYS. If you have access to one, you can create the file $HOME/.licenses/ansys.lic with the license information. If you think you should have access to one as part of your project, contact ccr-help@buffalo.edu. For more information about configuring an ANSYS license, please see https://docs.ccr.buffalo.edu/en/latest/software/modules/#application-specific-notes#ansys

	]]
	LmodError(error_message)
elseif (path) then
	-- load the license file which should contain Lua commands to set the license path
	assert(loadfile(path))()
end
"""

def get_ccr_envvar(ccr_envvar):
    """Get an CCR environment variable from the environment"""

    ccr_envvar_value = os.getenv(ccr_envvar)
    if ccr_envvar_value is None:
        raise EasyBuildError("$%s is not defined!", ccr_envvar)

    return ccr_envvar_value

def set_modluafooter(ec):
    software_path = get_ccr_envvar('CCR_EASYBUILD_PATH')
    ccr_version = get_ccr_envvar('CCR_VERSION')
    eprefix = get_ccr_envvar('EPREFIX')
    moduleclass = ec.get('moduleclass','')
    name = ec['name'].lower()

    if name == 'easybuild':
        ec['modluafooter'] += (CUSTOMEB_MODLUAFOOTER)

    if name == 'anaconda3':
        ec['modluafooter'] += (ANACONDA_MODLUAFOOTER)

    if name == 'pavilion':
        ec['modluafooter'] += (PAVILION_MODLUAFOOTER)

    if name == 'ansys':
        ebrootx11 = get_ccr_envvar('EBROOTX11')
        ec['modluafooter'] += ANSYS_MODLUAFOOTER.format(eprefix=eprefix, ebrootx11=ebrootx11)

    if name == 'openmpi':
        if ec['toolchain']['name'].lower() == 'nvhpc':
            nvhpcver = get_ccr_envvar('EBVERSIONNVHPC')
            comp = os.path.join('MPI', 'nvhpc', nvhpcver, name, ec['version'])
        else:
            gccver = get_ccr_envvar('EBVERSIONGCC')
            comp = os.path.join('MPI', 'gcc', gccver, name, ec['version'])

        ec['modluafooter'] += MPI_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, sub_path=comp)

    if name == 'matlab':
        ec['modluafooter'] += MATLAB_MODLUAFOOTER.format(eprefix=eprefix)

    if name == 'gurobi':
        ec['modluafooter'] += GUROBI_MODLUAFOOTER.format()

    if moduleclass == 'compiler':
        if name in ['iccifort', 'intel-compilers']:
            name = 'intel'
        comp = os.path.join('Compiler', name, ec['version'])
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
    self.cfg.enhance_sanity_check = True

def get_rpath_override_dirs(software_name):
    # determine path to installations in software layer via $CCR_EASYBUILD_PATH
    ccr_software_path = get_ccr_envvar('CCR_EASYBUILD_PATH')
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

    if 'cuda' in self.full_mod_name.lower():
        print_msg("Module requires cuda so adding /opt/software/nvidia/lib64 to rpath")
        update_build_option('rpath_override_dirs', '/opt/software/nvidia/lib64')


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
    if ec.name == 'CUDA' or ec.name == 'cuDNN':
        ec.update('builddependencies', [('GCCcore', '11.2.0')])
        print_msg("Using custom build deps for %s: %s", ec.name, ec['builddependencies'])
    else:
        raise EasyBuildError("cuda-specific hook triggered for non-cuda easyconfig?!")

def perl_config_opts(ec, prefix):
    """Custom config options for Perl."""
    if ec.name != 'Perl':
        raise EasyBuildError("perl-specific hook triggered for non-perl easyconfig?!")

    print_msg(f"Set path to openssl in compat layer for Perl {ec.version}..")
    # XXX is this still necessary?
#    setvar("EBROOTOPENSSL", f"{prefix}/usr")

def gurobi_config_opts(ec, prefix):
    """Custom config options for Gurobi."""
    if ec.name != 'Gurobi':
        raise EasyBuildError("gurobi-specific hook triggered for non-gurobi easyconfig?!")

    ec['license_file'] = '/util/software/licenses/gurobi.lic'

def hdf5_config_opts(ec, prefix):
    """Custom config options for HDF5."""
    if ec.name != 'HDF5':
        raise EasyBuildError("hdf5-specific hook triggered for non-hdf5 easyconfig?!")

    if ec.toolchain.mpi_family():
        # If building hdf5 with parallel mpi support we need to explicity set mpicxx here
        ec.update('configopts', 'CXX=mpicxx ')

def pillow_preconfig(ec, *args, **kwargs):
    """Custom config options for Pillow."""
    if ec.name != 'Pillow' and ec.name != 'Pillow-SIMD':
        raise EasyBuildError("Pillow-specific hook triggered for non-Pillow easyconfig?!")

    setvar("LDFLAGS", '-L/cvmfs/soft.ccr.buffalo.edu/versions/2023.01/compat/usr/lib64')

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
        print_msg("Using custom configure option for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("pmix-specific hook triggered for non-pmix easyconfig?!")

def gdal_config_opts(ec, eprefix):
    """Inject configure options for gdal."""
    if ec.name == 'GDAL':
        ec.update('configopts', '--with-libjson-c=%s' % os.path.join(eprefix, 'usr'))
        print_msg("Using custom configure option for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("gdal-specific hook triggered for non-gdal easyconfig?!")

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

def povray_eprefix(ec, eprefix):
    """Fix POV-Ray setting default system path to /usr for X11 via added configuration options."""
    if ec.name == 'POV-Ray':
        ec.update('configopts', '--x-includes=$EBROOTX11/include --x-libraries=$EBROOTX11/lib')
        print_msg("Adding custom configure options for %s: %s", ec.name, ec['configopts'])
    else:
        raise EasyBuildError("POV-Ray specific hook to overcome hardcoded system /usr path for X11 ")

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
            'echo "-nostdinc" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/icpc.cfg',
            'echo "-I$EBROOTGCCCORE/lib/gcc/x86_64-pc-linux-gnu/$EBVERSIONGCCCORE/include" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/icpc.cfg',
            'echo "-I$EBROOTGCCCORE/include/c++/$EBVERSIONGCCCORE" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/icpc.cfg',
            'echo "-I$EBROOTGCCCORE/include/c++/$EBVERSIONGCCCORE/x86_64-pc-linux-gnu" >> %(installdir)s/compiler/%(version)s/linux/bin/intel64/icpc.cfg',
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
        ec.cfg['set_mpi_wrappers_all'] = True
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
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin --add_path="/opt/software/nvidia/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("matlab-specific hook triggered for non-matlab easyconfig?!")

def nvidia_rpath_postproc(ec, *args, **kwargs):
    """Add post install cmds to set the RPATH to the nVidia libraries."""

    ccr_init = get_ccr_envvar('CCR_INIT_DIR')
    ec.cfg['postinstallcmds'] = [
        'chmod -R u+w %(installdir)s',
        f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin --add_path="/opt/software/nvidia/lib64"',
    ]
    print_msg("Using custom postproc command to set the RPATH to the nVidia libraries for %s: %s", ec.name, ec.cfg['postinstallcmds'])

def cuda_postproc(ec, *args, **kwargs):
    """Add post install cmds for cuda."""

    if ec.name == 'CUDA' or ec.name == 'cuDNN':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin --add_path="/opt/software/nvidia/lib64:$EBROOTGCCCORE/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("cuda-specific hook triggered for non-cuda easyconfig?!")

def tensorflow_postproc(ec, *args, **kwargs):
    """Add post install cmds for TensorFlow."""

    if ec.name == 'TensorFlow':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_origin --add_path="/opt/software/nvidia/lib64:$EBROOTCUDA/lib64:$EBROOTNCCL/lib:$EBROOTCUDNN/lib"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("tensorflow-specific hook triggered for non-cuda easyconfig?!")

def nvhpc_postproc(ec, *args, **kwargs):
    """Add post install cmds for nvhpc."""

    if ec.name == 'NVHPC':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/Linux_x86_64/%(version)s --add_path="/opt/software/nvidia/lib64:$EBROOTCUDA/lib64:$EPREFIX/lib64"',
            f'echo "set DEFLIBDIR=$EPREFIX/usr/lib64;" >> %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
            f'echo "set DEFSTDOBJDIR=$EPREFIX/usr/lib64;" >> %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
#            f'sed -i "\@^set LC=@s@-lgcc@-rpath=/opt/software/nvidia/lib64:$EBROOTGCCCORE/lib64:$EPREFIX/lib64 -lgcc@" %(installdir)s/Linux_x86_64/%(version)s/compilers/bin/localrc',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("nvhpc-specific hook triggered for non-nvhpc easyconfig?!")

def clang_preconfig(ec, *args, **kwargs):
    """Add preconfig cmds for clang."""

    if ec.name == 'Clang':
        ec.cfg['preconfigopts'] = ("""pushd %(builddir)s/llvm-%(version)s.src/tools/clang || pushd %(builddir)s/llvm-project-%(version)s.src/clang; """ +
            # Use ${EPREFIX} as default sysroot
            """sed -i -e "s@DEFAULT_SYSROOT \\"\\"@DEFAULT_SYSROOT \\"${EPREFIX}\\"@" CMakeLists.txt ; """ +
            """pushd lib/Driver/ToolChains ; """ +
            # Use dynamic linker from ${EPREFIX}
            """sed -i -e "/LibDir.*Loader/s@return \\"\/\\"@return \\"${EPREFIX%/}/\\"@" Linux.cpp ; """ +
            # Remove --sysroot call on ld for native toolchain
            """sed -i -e "$(grep -n -B1 sysroot= Gnu.cpp | sed -ne '{1s/-.*//;1p}'),+1 d" Gnu.cpp ; """ +
            """popd; popd ; """)
        print_msg("Using custom preconfig commands for %s: %s", ec.name, ec.cfg['preconfigopts'])
    else:
        raise EasyBuildError("clang-specific hook triggered for non-clang easyconfig?!")

def gurobi_postproc(ec, *args, **kwargs):
    """Add post install cmds for Gurobi."""

    if ec.name == 'Gurobi':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/bin --add_path='$ORIGIN/../lib'",
            f"{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/lib/python3.9/site-packages/gurobipy --add_path='$ORIGIN/../../../../lib'",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("gurobi-specific hook triggered for non-Gurobi easyconfig?!")

def vtune_postproc(ec, *args, **kwargs):
    """Add post install cmds for VTune."""

    if ec.name == 'VTune':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/vtune --add_origin --add_path="$EPREFIX/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("vtune-specific hook triggered for non-vtune easyconfig?!")

def jax_postproc(ec, *args, **kwargs):
    """Add post install cmds for jax when install via pip wheels."""

    # XXX note this should only be done when installing via binary pip wheels
    if ec.name == 'jax':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/lib --add_origin --add_path="/opt/software/nvidia/lib64:$EBROOTGCCCORE/lib64:$EPREFIX/lib64:$EBROOTCUDA/lib64:$EBROOTCUDNN/lib"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("jax-specific hook triggered for non-jax easyconfig?!")

def niftypet_postproc(ec, *args, **kwargs):
    """Add post install cmds for niftypet"""

    if ec.name == 'NiftyPET':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/lib --add_path="/opt/software/nvidia/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("niftypet-specific hook triggered for non-niftypet easyconfig?!")

def openmolcas_postproc(ec, *args, **kwargs):
    if ec.name == 'OpenMolcas':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/bin --add_path="%(installdir)s/qcmaquis/lib" --any_interpreter',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("openmolcas-specific hook triggered for non-openmolcas easyconfig?!")

def paraview_postproc(ec, *args, **kwargs):
    """Add post install cmds for paraview"""

    if ec.name == 'ParaView':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/lib64/ --add_origin --add_path="$EBROOTGCCCORE/lib64:$EPREFIX/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("paraview-specific hook triggered for non-paraview easyconfig?!")

def mathematica_postproc(ec, *args, **kwargs):
    """Add post install cmds for mathematica"""

    if ec.name == 'Mathematica':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/SystemFiles/FrontEnd/Binaries/Linux-x86-64/ --add_origin --add_path="/opt/software/nvidia/lib64:$EBROOTX11/lib64:$EBROOTFREETYPE/lib64:$EBROOTFONTCONFIG/lib64:$EPREFIX/usr/lib64:$EPREFIX/lib64"',
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/SystemFiles/Libraries/Linux-x86-64/Qt/lib/ --add_path="/opt/software/nvidia/lib64:$EBROOTX11/lib64:$EPREFIX/usr/lib64:$EPREFIX/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("mathematica-specific hook triggered for non-mathematica easyconfig?!")

def cupy_postproc(ec, *args, **kwargs):
    """Add post install cmds for cupy."""

    if ec.name == 'CuPy':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s/lib --add_path="/opt/software/nvidia/lib64"',
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("cupy-specific hook triggered for non-cuda easyconfig?!")

def ansys_postproc(ec, *args, **kwargs):
    """Add post install cmds for ansys"""

    if ec.name == 'ANSYS':
        ccr_init = get_ccr_envvar('CCR_INIT_DIR')
        ec.cfg['postinstallcmds'] = [
            # Fix setmwruntime path and X11 lib dir
            'sed -i "s#X11_LIB_DIR=/usr/X11R6/lib64#X11_LIB_DIR=$EBROOTX11/lib#g" %(installdir)s/v231/commonfiles/MainWin/linx64/mw/setmwruntime',
            'sed -i "s#PATH=\"\$PATH:/usr/bin/X11\"#PATH=\"$EPREFIX/bin:$EPREFIX/usr/bin:$EBROOTX11/bin:\$PATH\"#g" %(installdir)s/v231/commonfiles/MainWin/linx64/mw/setmwruntime',
            'chmod 755 %(installdir)s/v231/commonfiles/MainWin/linx64/mw/setmwruntime',
            # Set same perms on all directories
            "find %(installdir)s -type d -exec chmod 755 {} \;",
            # Set same perms on all shared libraries to avoid warning in log file
            "find %(installdir)s -type f \( -name '*.so' -o -name '*.so.*' \) -exec chmod 755 {} \;",
            # Rename some libs as these maybe older than system equivalents and missing new symbols
            "find %(installdir)s \( -type f -o -type l \) -name 'libstdc++.so*' -exec mv {} {}.bak \;",
            "find %(installdir)s \( -type f -o -type l \) -name 'libgcc_s.so*' -exec mv {} {}.bak \;",
            "find %(installdir)s \( -type f -o -type l \) -name 'libfreetype*' -exec mv {} {}.bak \;",
            "find %(installdir)s \( -type f -o -type l \) -name 'libgfortran.so*' -exec mv {} {}.bak \;",
            "find %(installdir)s \( -type f -o -type l \) -name 'libgfortran.so.3*bak' -print0 | while IFS= \
            read -r -d $'\\0' file; do echo \"Removing bak from $file\"; mv \"$file\" \"${file%.bak}\"; done;",
            # Find all non-binary files containing  [:"]/usr/lib or [:"]/lib on one line and remove them from the paths
            "for f in $(grep -rIl '[:\"]/usr/lib\|[:\"]/lib' %(installdir)s); do echo Modifying file $f; \
            sed -i -e '/[:\"]\/usr\/lib/s/:*\/usr\/lib[^:\"]*//g' -e '/[:\"]\/lib/s/:*\/lib[^:\"]*//g' $f; done",
            # Run setrpaths.sh in all directories
            f'{ccr_init}/easybuild/setrpaths.sh --path %(installdir)s --add_path="/opt/software/nvidia/lib64:$EBROOTX11/lib64:$EBROOTGCCCORE/lib64:$EPREFIX/usr/lib64:$EPREFIX/lib64"',
            # Run setrpaths.sh for any_interpreter
            f"find %(installdir)s -type f \( -name 'lmutil' -o -name 'lmgrd' -o -name 'NTI' \) -exec {ccr_init}/easybuild/setrpaths.sh --path {{}} --any_interpreter \;",
            # Avoid warning starting workbench mechanical: sh: domainname: command not found
            "cd %(installdir)s/v231/Tools/mono/Linux64/bin; ln -s $EPREFIX/bin/hostname domainname",
            # Replace '/bin/sh' with '$EPREFIX/bin/sh'
            "find %(installdir)s -type f ! -size 0 -not -name 'fluent.dmp*' -not -name 'flprim.dmp*' -print0 | \
            xargs -0 grep -riIlZ '/bin/sh' | while IFS= read -r -d $'\\0' file; do echo \"$file\"; \
            sed -i \"s|/bin/sh|$EPREFIX/bin/sh|g\" \"$file\"; done;",
            # Replace '/bin/bash' with '$EPREFIX/bin/bash'
            "find %(installdir)s -type f ! -size 0 -not -name 'fluent.dmp*' -not -name 'flprim.dmp*' -print0 | \
            xargs -0 grep -riIlZ '/bin/bash' | while IFS= read -r -d $'\\0' file; do echo \"$file\"; \
            sed -i \"s|/bin/bash|$EPREFIX/bin/bash|g\" \"$file\"; done;",
            # Remove /sbin/ from both of the /sbin/lspci entries inside libApipWrapper.so
            "find %(installdir)s -type f ! -size 0 -name 'libApipWrapper.so' -print0 | xargs -0 \
            grep -rilZ '/sbin/lspci' | while IFS= read -r -d $'\\0' file; do echo \"$file\"; \
            perl -0777 -pe 's/\/sbin\//substr q{}.\"\\0\"x length$&,0,length$&/e or die \"pattern not found\"' -i \"$file\"; \
            perl -0777 -pe 's/\/sbin\//substr q{}.\"\\0\"x length$&,0,length$&/e or die \"pattern not found\"' -i \"$file\"; done;",
            # Avoid warning when starting workbench: Unit[s] is not valid for quantity Time
            "cd %(installdir)s/v231/tp/CUEUnits/linx64/lib;\
            mv libCUEUnits.so libCUEUnits.so-orig;\
            ln -s ../../../../aisol/lib/linx64/libCUEUnits.so libCUEUnits.so;",
            # Avoid cfx-pre warning: libjpeg.so.62: no version information available
            "cd %(installdir)s/v231/tp/qt/5.9.6/linx64/lib;\
            mv libjpeg.so.62.0.0 libjpeg.so.62.0.0-orig;\
            mv libjpeg.so.62 libjpeg.so.62-orig;\
            ln -s $EPREFIX/usr/lib64/libjpeg.so.62 libjpeg.so.62;",
            # Fix ld preload errors
            """sed -i '/^   LD_PRELOAD="${SysLibStdCpp/d' %(installdir)s/v231/ansys/bin/anssh.ini""",
        ]
        print_msg("Using custom postproc command option for %s: %s", ec.name, ec.cfg['postinstallcmds'])
    else:
        raise EasyBuildError("ansys-specific hook triggered for non-ansys easyconfig?!")

PARSE_HOOKS = {
    'fontconfig': fontconfig_add_fonts,
    'UCX': ucx_eprefix,
    'POV-Ray': povray_eprefix,
    'OpenMPI': openmpi_config_opts,
    'OpenBLAS': openblas_config_opts,
    'PMIx': pmix_config_opts,
    'CUDA': cuda_config_opts,
    'cuDNN': cuda_config_opts,
    'Perl': perl_config_opts,
    'GDAL': gdal_config_opts,
    'Gurobi': gurobi_config_opts,
    'HDF5': hdf5_config_opts,
}

PRE_CONFIGURE_HOOKS = {
    'Clang': clang_preconfig,
    'Pillow': pillow_preconfig,
    'Pillow-SIMD': pillow_preconfig,
}

PRE_POSTPROC_HOOKS = {
    'iccifort': iccifort_postproc,
    'impi': impi_postproc,
    'imkl': imkl_postproc,
    'intel-compilers': intel_postproc,
    'intel': intel_postproc,
    'MATLAB': matlab_postproc,
    'CUDA': cuda_postproc,
    'cuDNN': cuda_postproc,
    'NVHPC': nvhpc_postproc,
    'Gurobi': gurobi_postproc,
    'VTune': vtune_postproc,
    'TensorFlow': tensorflow_postproc,
    'jax': jax_postproc,
    'NiftyPET': niftypet_postproc,
    'OpenMolcas': openmolcas_postproc,
    'ParaView': paraview_postproc,
    'Mathematica': mathematica_postproc,
    'CuPy': cupy_postproc,
    'ANSYS': ansys_postproc,
    'ont-guppy': nvidia_rpath_postproc,
}
