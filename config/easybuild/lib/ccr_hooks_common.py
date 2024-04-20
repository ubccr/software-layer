import os
from collections.abc import Hashable
from enum import Enum,auto
from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.config import build_option, update_build_option

class Op(Enum):
    REPLACE = auto()
    PREPEND = auto()
    APPEND = auto()
    DROP = auto()
    APPEND_LIST = auto()
    PREPEND_LIST = auto()
    DROP_FROM_LIST = auto()
    REPLACE_IN_LIST = auto()

CCR_RPATH_OVERRIDE_ATTR = 'orig_rpath_override_dirs'
# options to change in parse_hook, others are changed in other hooks
PARSE_OPTS = ['multi_deps', 'dependencies', 'builddependencies', 'license_file', 'version', 'name',
              'source_urls', 'sources', 'patches', 'checksums', 'versionsuffix', 'modaltsoftname',
              'skip_license_file_in_module', 'withnvptx', 'skipsteps', 'testops']

class Dep:
    def __init__(self, name, to_version, from_version=None, suffix='', toolchain=None):
        self.name = name
        self.to_version = to_version
        self.from_version =from_version
        self.suffix = suffix
        self.toolchain = toolchain

    def to_tuple(self):
        if self.toolchain != None and isinstance(self.toolchain, tuple):
            return (self.name, self.to_version, self.suffix, self.toolchain)

        return (self.name, self.to_version)


def get_ccr_envvar(ccr_envvar):
    """Get an CCR environment variable from the environment"""

    ccr_envvar_value = os.getenv(ccr_envvar)
    if ccr_envvar_value is None:
        raise EasyBuildError("$%s is not defined!", ccr_envvar)

    return ccr_envvar_value

def hook_call(name, hooks, ec, *args, **kwargs):
    if ec.name in hooks and name in hooks[ec.name]:
        hooks[ec.name][name](ec, *args, **kwargs)

def modify_dependencies(ec, deps):
    for new_dep in deps:
        modify_dep(ec, new_dep)

def modify_dep(ec, new_dep):
    for key in ['dependencies', 'hiddendependencies', 'builddependencies']:
        for index in range(len(ec[key])):
            dep = ec[key][index]
            if isinstance(dep, (list,tuple)) and dep[0] == new_dep.name:
                if new_dep.from_version != None and dep[1] != new_dep.from_version:
                    continue

                print_msg(f"{new_dep.name} {key} version has been modified from {dep[0]}/{dep[1]} --> {new_dep.name}/{new_dep.to_version}")
                ec[key][index] = new_dep.to_tuple()

# All code below here copied from:
# https://github.com/ComputeCanada/easybuild-computecanada-config/blob/main/cc_hooks_common.py
def get_matching_keys_from_ec(ec, dictionary):
    if 'modaltsoftname' in ec:
        matching_keys = get_matching_keys(ec['modaltsoftname'], ec['version'], ec['versionsuffix'], dictionary)
    if not matching_keys:
        matching_keys = get_matching_keys(ec['name'], ec['version'], ec['versionsuffix'], dictionary)
    return matching_keys

def get_matching_keys(name, version, versionsuffix, dictionary):
    matching_keys = []
    #version can sometimes be a dictionary, which is not hashable
    if isinstance(version, Hashable):
        try_keys = [(name, version, versionsuffix), (name, version), (name, 'ANY', versionsuffix), name ]
    else:
        try_keys = [(name, 'ANY', versionsuffix), name]
    matching_keys = [key for key in try_keys if key in dictionary]

    return matching_keys

def modify_all_opts(ec, opts_changes, opts_to_skip=None, opts_to_change='ALL'):
    matching_keys = get_matching_keys_from_ec(ec, opts_changes)

    if opts_to_skip is None:
        opts_to_skip = []
    for key in matching_keys:
        if key in opts_changes.keys():
            for opt, value in opts_changes[key].items():
                # we don't modify those in this stage
                if opt in opts_to_skip:
                    continue
                if opts_to_change == 'ALL' or opt in opts_to_change:
                    if isinstance(value, list):
                        values = value
                    else:
                        values = [value]

                    for v in values:
                        update_opts(ec, v[0], opt, v[1])
            break

def update_opts(ec,changes,key, update_type):
    if key not in ec:
        return
    orig = ec[key]
    if update_type == Op.REPLACE:
        ec[key] = changes
    elif update_type in [Op.APPEND_LIST, Op.PREPEND_LIST, Op.DROP_FROM_LIST, Op.REPLACE_IN_LIST]:
        if not isinstance(changes,list):
            changes = [changes]
        for change in changes:
            if update_type == Op.APPEND_LIST:
                ec[key].append(change)
            elif update_type == Op.DROP_FROM_LIST:
                ec[key] = [x for x in ec[key] if x not in changes]
            elif update_type == Op.REPLACE_IN_LIST:
                for swap in changes:
                    ec[key] = [swap[1] if x == swap[0] else x for x in ec[key]]
            else:
                ec[key].insert(0, change)
    else:
        if isinstance(ec[key], str):
            opts = [ec[key]]
        elif isinstance(ec[key], list):
            opts = ec[key]
        else:
            return
        for i in range(len(opts)):
            if not changes in opts[i]:
                if update_type == Op.PREPEND:
                    opts[i] = changes + opts[i]
                elif update_type == Op.APPEND:
                    opts[i] = opts[i] + changes
            elif update_type == Op.DROP:
                opts[i] = opts[i].replace(changes,'')

        if isinstance(ec[key], str):
            ec[key] = opts[0]

    if str(ec[key]) != str(orig):
        print_msg("%s: Changing %s from: %s to: %s" % (ec.filename(),key,orig,ec[key]))
