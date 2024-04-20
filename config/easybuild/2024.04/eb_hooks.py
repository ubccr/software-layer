# Hooks to customize how EasyBuild installs software in CCR
# see https://docs.easybuild.io/en/latest/Hooks.html
import os
import sys

from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.config import build_option, update_build_option

thisdir = os.path.dirname(__file__)
if thisdir not in sys.path:
    sys.path.append(thisdir)

libdir = os.path.join(os.path.dirname(thisdir), 'lib')
if libdir not in sys.path:
    sys.path.append(libdir)

from ccrsoft import DEPS, HOOKS, CHANGES, COMPILER_MODLUAFOOTER, MPI_MODLUAFOOTER
from ccr_hooks_common import (hook_call, get_ccr_envvar, get_matching_keys_from_ec, modify_dependencies, 
                              modify_all_opts, PARSE_OPTS, CCR_RPATH_OVERRIDE_ATTR)

def set_modluafooter(ec):
    software_path = get_ccr_envvar('CCR_EASYBUILD_PATH')
    ccr_version = get_ccr_envvar('CCR_VERSION')
    cpu_family = get_ccr_envvar('CCR_CPU_FAMILY')
    eprefix = get_ccr_envvar('EPREFIX')
    moduleclass = ec.get('moduleclass','')
    name = ec['name'].lower()

    matching_keys = get_matching_keys_from_ec(ec, CHANGES)
    for key in matching_keys:
        for opt in ('modluafooter', 'allow_prepend_abs_path', 'modextrapaths', 'ebpythonprefixes'):
            if opt in CHANGES[key]:
                update_opts(ec, CHANGES[key][opt][0], opt, CHANGES[key][opt][1])

    if moduleclass == 'compiler':
        if name in ['iccifort', 'intel-compilers']:
            name = 'intel'
        comp = os.path.join('Compiler', name, ec['version'])
        ec['modluafooter'] += COMPILER_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, cpu_family=cpu_family, sub_path=comp)

    if name == 'openmpi':
        if ec['toolchain']['name'].lower() == 'nvhpc':
            nvhpcver = get_ccr_envvar('EBVERSIONNVHPC')
            comp = os.path.join('MPI', 'nvhpc', nvhpcver, name, ec['version'])
        else:
            gccver = get_ccr_envvar('EBVERSIONGCC')
            comp = os.path.join('MPI', 'gcc', gccver, name, ec['version'])

        ec['modluafooter'] += MPI_MODLUAFOOTER.format(software_path=software_path, ccr_version=ccr_version, cpu_family=cpu_family, sub_path=comp)

def parse_hook(ec, *args, **kwargs):
    modify_dependencies(ec, DEPS)
    modify_all_opts(ec, CHANGES, opts_to_change=PARSE_OPTS)

    hook_call('parse_hook', HOOKS, ec, *args, **kwargs)

def pre_module_hook(self, *args, **kwargs):
    "Modify module footer (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    set_modluafooter(self.cfg)
    self.cfg.enable_templating = orig_enable_templating
    self.cfg.enhance_sanity_check = True

    hook_call('pre_module_hook', HOOKS, self, *args, **kwargs)

def pre_prepare_hook(self, *args, **kwargs):
    """Main pre-prepare hook: trigger custom functions."""

    hook_call('pre_prepare_hook', HOOKS, self, *args, **kwargs)

def pre_configure_hook(self, *args, **kwargs):
    "Modify configopts (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False

    modify_all_opts(self.cfg, CHANGES, opts_to_skip=PARSE_OPTS + ['exts_list',
                                                            'postinstallcmds',
                                                            'modluafooter',
                                                            'ebpythonprefixes',
                                                            'allow_prepend_abs_path',
                                                            'modextrapaths'])

    self.cfg.enable_templating = orig_enable_templating
    hook_call('pre_configure_hook', HOOKS, self, *args, **kwargs)

def pre_fetch_hook(self, *args, **kwargs):
    "Modify extension list (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    modify_all_opts(self.cfg, CHANGES, opts_to_change=['exts_list'])
    self.cfg.enable_templating = orig_enable_templating

    hook_call('pre_fetch_hook', HOOKS, self, *args, **kwargs)

def pre_postproc_hook(self, *args, **kwargs):
    "Modify postinstallcmds (here is more efficient than parse_hook since only called once)"
    orig_enable_templating = self.cfg.enable_templating
    self.cfg.enable_templating = False
    modify_all_opts(self.cfg, CHANGES, opts_to_change=['postinstallcmds'])
    self.cfg.enable_templating = orig_enable_templating

    hook_call('pre_postproc_hook', HOOKS, self, *args, **kwargs)

def post_prepare_hook(self, *args, **kwargs):
    """Main post-prepare hook: trigger custom functions."""

    if hasattr(self, CCR_RPATH_OVERRIDE_ATTR):
        # Reset the value of 'rpath_override_dirs' now that we are finished with it
        update_build_option('rpath_override_dirs', getattr(self, CCR_RPATH_OVERRIDE_ATTR))
        print_msg("Resetting rpath_override_dirs to original value: %s", getattr(self, CCR_RPATH_OVERRIDE_ATTR))
        delattr(self, CCR_RPATH_OVERRIDE_ATTR)

    hook_call('post_prepare_hook', HOOKS, self, *args, **kwargs)

def pre_test_hook(self, *args, **kwargs):
    """Main pre-test hook: trigger custom functions based on software name."""
    hook_call('pre_test_hook', HOOKS, self, *args, **kwargs)
