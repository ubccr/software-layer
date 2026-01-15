#!/usr/bin/env python3

import os
import archspec.cpu
from archspec.cpu.detect import compatible_microarchitectures, raw_info_dictionary

# XXX legacy microarch remove soon
MICRO_ARCH_MAP_LEGACY = [
	('x86_64_v4', 'avx512'),
	('x86_64_v3', 'avx2'),
]

MICRO_ARCH_MAP = [
	('x86_64_v4', 'x86-64-v4'),
	('x86_64_v3', 'x86-64-v3'),
	('cortex_a72', 'neoverse-v2'),
]

def host_arch():
    ccrver = os.environ.get('CCR_VERSION', '2023.01')

    micro_map = MICRO_ARCH_MAP
    if ccrver == '2023.01':
        micro_map = MICRO_ARCH_MAP_LEGACY

    raw_cpu_info = raw_info_dictionary()
    compat_targets = compatible_microarchitectures(raw_cpu_info)

    for march in micro_map:
        if march[0] in compat_targets:
            return march[1]

    return 'generic'

def main():
    arch = host_arch()
    print(arch)

if __name__ == '__main__':
    main()
