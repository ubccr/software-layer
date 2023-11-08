help([[Gentoo prefix is Gentoo Linux installed in a prefix - Homepage: https://wiki.gentoo.org/wiki/Project:Prefix]])
whatis("Gentoo prefix is Gentoo Linux installed in a prefix - Homepage: https://wiki.gentoo.org/wiki/Project:Prefix")

require("SitePackage")
add_property(   "lmod", "sticky")

local ccr_compat_version ="2022.05"
local ccr_repo_path = os.getenv("CCR_CVMFS_REPO")
local root = pathJoin(ccr_repo_path, "versions", ccr_compat_version, "compat")
setenv("EPREFIX", root)

prepend_path("PATH", pathJoin(root, "bin"))
prepend_path("PATH", pathJoin(root, "sbin"))
prepend_path("PATH", pathJoin(root, "usr/bin"))
prepend_path("PATH", pathJoin(root, "usr/sbin"))
prepend_path("PATH", "/opt/software/nvidia/bin")
prepend_path("PATH", "/opt/software/bin")
prepend_path("INFOPATH", pathJoin(root, "usr/share/binutils-data/x86_64-pc-linux-gnu/2.38/info:"))
prepend_path("MANPATH", pathJoin(root, "usr/share/man"))
prepend_path("MANPATH", pathJoin(root, "usr/local/share/man"))
prepend_path("MANPATH", pathJoin(root, "usr/share/binutils-data/x86_64-pc-linux-gnu/2.38/man"))
prepend_path("MANPATH", pathJoin(root, "usr/share/gcc-data/x86_64-pc-linux-gnu/11.3.0/man"))
