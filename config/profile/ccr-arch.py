#!/usr/bin/env python3

from archspec.cpu.detect import compatible_microarchitectures, raw_info_dictionary

def host_arch():
    def sorting_fn(item):
        """Helper function to sort compatible microarchitectures."""
        return len(item.ancestors), len(item.features)

    raw_cpu_info = raw_info_dictionary()
    compat_targets = compatible_microarchitectures(raw_cpu_info)

    # filter out generic targets
    non_generic_compat_targets = [t for t in compat_targets if t.vendor != "generic"]

    # Filter the candidates to be descendant of the best generic candidate
    best_generic = max([t for t in compat_targets if t.vendor == "generic"], key=sorting_fn)
    best_compat_targets = [t for t in non_generic_compat_targets if t > best_generic]

    if best_compat_targets:
        host_cpu = max(best_compat_targets, key=sorting_fn)
    else:
        host_cpu = max(non_generic_compat_targets, key=sorting_fn)

    if 'avx512f' in host_cpu.features:
        return "avx512"
    elif 'avx2' in host_cpu.features:
        return "avx2"
    elif 'avx' in host_cpu.features:
        return "avx"
    elif 'pni' in host_cpu.features:
        return "sse3"
    return "sse3"

def main():
    arch = host_arch()
    print(arch)

if __name__ == '__main__':
    main()
