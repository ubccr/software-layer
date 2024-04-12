help([==[

Description
===========
CCR 2024.04 Software release.


More information
================
 - Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/
]==])

whatis([==[Description: CCR 2024.04 Software release]==])
whatis([==[Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])
whatis([==[URL: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])

local ccr_version ="2024.04"
local arch = os.getenv("CCR_ARCH")
local ccr_repo_path = os.getenv("CCR_CVMFS_REPO")
local ccr_os_type = os.getenv("CCR_OS_TYPE")
local ccr_cpu_family = os.getenv("CCR_CPU_FAMILY")
local ccr_prefix = pathJoin(ccr_repo_path, "versions", ccr_version)
local ccr_easybuild_path = pathJoin(ccr_prefix, "easybuild", ccr_cpu_family)
local ccr_banalbuild_path = pathJoin(ccr_prefix, "banalbuild", ccr_cpu_family)

setenv("CCR_VERSION", ccr_version)
setenv("CCR_PREFIX", ccr_prefix)
setenv("CCR_EASYBUILD_PATH", ccr_easybuild_path)
setenv("CCR_BANALBUILD_PATH", ccr_banalbuild_path)

if not arch or arch == "" then
    arch = get_highest_supported_architecture()
    setenv("CCR_ARCH", arch)
end

add_property("lmod", "sticky")
require("os")
require("SitePackage")
load("ccrenv")
load("gentoo/2024.04")

if (mode() ~= "spider") then
    prepend_path("MODULEPATH", pathJoin(ccr_easybuild_path, "modules/Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_easybuild_path, "modules", arch, "Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_banalbuild_path, "modules/Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_banalbuild_path, "modules", arch, "Core"))
    local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
    if customBuildPaths ~= nil then
        for customPath in customBuildPaths:split(":") do
            if isDir(pathJoin(customPath, ccr_version, "modules")) then
                prepend_path("MODULEPATH", pathJoin(customPath, ccr_version, ccr_cpu_family, "modules/Core"))
                prepend_path("MODULEPATH", pathJoin(customPath, ccr_version, ccr_cpu_family, "modules", arch, "Core"))
            end
        end
    end
    if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, "modules")) then
        prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, ccr_cpu_family, "modules/Core"))
        prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, ccr_cpu_family, "modules", arch, "Core"))
    end
end
