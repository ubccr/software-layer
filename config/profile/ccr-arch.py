#!/usr/bin/env python3

import archspec.cpu

def host_arch():
    host_cpu = archspec.cpu.host()
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
