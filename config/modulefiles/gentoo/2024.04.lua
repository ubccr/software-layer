help([[Gentoo prefix is Gentoo Linux installed in a prefix - Homepage: https://wiki.gentoo.org/wiki/Project:Prefix]])
whatis("Gentoo prefix is Gentoo Linux installed in a prefix - Homepage: https://wiki.gentoo.org/wiki/Project:Prefix")

require("SitePackage")
add_property(   "lmod", "sticky")

local ccr_compat_version ="2024.04"
local ccr_os_type = os.getenv("CCR_OS_TYPE") or "linux"
local ccr_cpu_family = os.getenv("CCR_CPU_FAMILY") or "x86_64"
local ccr_repo_path = os.getenv("CCR_CVMFS_REPO")
local root = pathJoin(ccr_repo_path, 'versions', ccr_compat_version, 'compat', ccr_os_type, ccr_cpu_family)
setenv("EPREFIX", root)

local os_data_path = "x86_64-pc-linux-gnu"
if (ccr_cpu_family == "aarch64") then
    os_data_path = "aarch64-unknown-linux-gnu"
end

prepend_path("PATH", pathJoin(root, "bin"))
prepend_path("PATH", pathJoin(root, "sbin"))
prepend_path("PATH", pathJoin(root, "usr/bin"))
prepend_path("PATH", pathJoin(root, "usr/sbin"))
prepend_path("PATH", "/opt/software/nvidia/bin")
prepend_path("PATH", "/opt/software/bin")
prepend_path("INFOPATH", pathJoin(root, "usr/share/binutils-data", os_data_path, "2.42/info:"))
prepend_path("MANPATH", pathJoin(root, "usr/share/man"))
prepend_path("MANPATH", pathJoin(root, "usr/local/share/man"))
prepend_path("MANPATH", pathJoin(root, "usr/share/binutils-data", os_data_path, "2.42/man"))
prepend_path("MANPATH", pathJoin(root, "usr/share/gcc-data", os_data_path, "11/man"))
prepend_path("XDG_DATA_DIRS", pathJoin(root, "usr/share"))
