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

local ccr_version_prev = os.getenv("CCR_VERSION") or "2024.04"
local ccr_version ="2024.04"
local arch = os.getenv("CCR_ARCH")
local ccr_repo_path = os.getenv("CCR_CVMFS_REPO")
local ccr_os_type = os.getenv("CCR_OS_TYPE")
local ccr_cpu_family = os.getenv("CCR_CPU_FAMILY")
local ccr_prefix = pathJoin(ccr_repo_path, "versions", ccr_version)
local ccr_easybuild_path = pathJoin(ccr_prefix, "easybuild", ccr_cpu_family)

local modrc = os.getenv("MODULERCFILE")
modrc = modrc:gsub('modulerc_'..ccr_version_prev..'.lua', 'modulerc_'..ccr_version..'.lua')
pushenv("MODULERCFILE", modrc)

pushenv("CCR_VERSION", ccr_version)
pushenv("CCR_PREFIX", ccr_prefix)
pushenv("CCR_EASYBUILD_PATH", ccr_easybuild_path)

if arch == "avx512" then
    arch = "x86-64-v4"
    setenv("CCR_ARCH", arch)
elseif arch == "avx2" then
    arch = "x86-64-v3"
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
