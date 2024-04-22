import os
from collections.abc import Hashable
from enum import Enum,auto
from easybuild.tools.build_log import EasyBuildError, print_msg
from easybuild.tools.config import build_option, update_build_option
from easybuild.tools.toolchain.utilities import search_toolchain
from easybuild.toolchains.system import SystemToolchain

class Op(Enum):
    REPLACE = auto()
    PREPEND = auto()
    APPEND = auto()
    DROP = auto()
    APPEND_LIST = auto()
    PREPEND_LIST = auto()
    DROP_FROM_LIST = auto()
    REPLACE_IN_LIST = auto()

# options to change in parse_hook, others are changed in other hooks
PARSE_OPTS = ['multi_deps', 'dependencies', 'builddependencies', 'license_file', 'version', 'name',
              'source_urls', 'sources', 'patches', 'checksums', 'versionsuffix', 'modaltsoftname',
              'skip_license_file_in_module', 'withnvptx', 'skipsteps', 'testops']

def get_ccr_envvar(ccr_envvar):
    """Get an CCR environment variable from the environment"""

    ccr_envvar_value = os.getenv(ccr_envvar)
    if ccr_envvar_value is None:
        raise EasyBuildError("$%s is not defined!", ccr_envvar)

    return ccr_envvar_value

def hook_call(name, hooks, ec, *args, **kwargs):
    if ec.name in hooks and name in hooks[ec.name]:
        hooks[ec.name][name](ec, *args, **kwargs)

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

def modify_list_of_dependencies(ec, param, version_mapping, list_of_deps):
    name = ec["name"]
    version = ec["version"]
    toolchain_name = ec.toolchain.name
    new_dep = None
    if not list_of_deps or not isinstance(list_of_deps[0], tuple): 
        print("Error, modify_list_of_dependencies did not receive a list of tuples")
        return

    for n, dep in enumerate(list_of_deps):
        if isinstance(dep,list): dep = dep[0]
        dep_name, dep_version, *rest = tuple(dep)
        dep_version_suffix = rest[0] if len(rest) > 0 else ""

        matching_keys = get_matching_keys(dep_name, dep_version, dep_version_suffix, version_mapping)
        # search through possible matching keys
        match_found = False
        for key in matching_keys:
            # Skip dependencies on the same name
            if name == key or name == key[0]:
                continue
            new_version, supported_toolchains, *new_version_suffix = version_mapping[key]
            new_version_suffix = new_version_suffix[0] if len(new_version_suffix) == 1 else dep_version_suffix

            # test if one of the supported toolchains is a subtoolchain of the toolchain with which we are building. If so, a match is found, replace the dependency
            supported_versions = [tc[1] for tc in supported_toolchains]
            for tc_name, tc_version in supported_toolchains:
                try_tc, _ = search_toolchain(tc_name)
                # for whatever reason, issubclass and class comparison does not work. It is the same class name, but not the same class, so comparing strings
                str_mro = [str(x) for x in ec.toolchain.__class__.__mro__]
                if try_tc == SystemToolchain or str(try_tc) in str_mro and ec.toolchain.version in supported_versions:
                    match_found = True
                    new_dep = (dep_name, new_version, new_version_suffix, (tc_name, tc_version))
                    if str(new_dep) != str(dep):
                        print("%s: Matching updated %s found. Replacing %s with %s" % (ec.filename(), param, str(dep), str(new_dep)))
                    list_of_deps[n] = new_dep
                    break

            if match_found: break

    return list_of_deps

def modify_dependencies(ec, param, version_mapping):
    name = ec["name"]
    version = ec["version"]
    toolchain_name = ec.toolchain.name
    if ec[param] and isinstance(ec[param][0], list) and ec[param][0] and isinstance(ec[param][0][0], tuple):
        for n, deps in enumerate(ec[param]):
            ec[param][n] = modify_list_of_dependencies(ec, param, version_mapping, ec[param][n])
    elif ec[param] and isinstance(ec[param][0], tuple):
        ec[param] = modify_list_of_dependencies(ec, param, version_mapping, ec[param])

def is_filtered_ec(ec):
    filter_spec = ec.parse_filter_deps()
    software_spec = {'name': ec.name, 'version': ec.version}
    return ec.dep_is_filtered(software_spec, filter_spec)
