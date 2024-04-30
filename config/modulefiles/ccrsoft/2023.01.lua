help([==[

Description
===========
CCR 2023.01 Software release.


More information
================
 - Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/
]==])

whatis([==[Description: CCR 2023.01 Software release]==])
whatis([==[Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])
whatis([==[URL: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])

local ccr_version ="2023.01"
local arch = os.getenv("CCR_ARCH") or ""
local ccr_repo_path = os.getenv("CCR_CVMFS_REPO")
local ccr_prefix = pathJoin(ccr_repo_path, "versions", ccr_version)
local ccr_easybuild_path = pathJoin(ccr_prefix, "easybuild")
local ccr_banalbuild_path = pathJoin(ccr_prefix, "banalbuild")

setenv("CCR_VERSION", ccr_version)
setenv("CCR_PREFIX", ccr_prefix)
setenv("CCR_EASYBUILD_PATH", ccr_easybuild_path)
setenv("CCR_BANALBUILD_PATH", ccr_banalbuild_path)

add_property("lmod", "sticky")
require("os")
require("SitePackage")
load("ccrenv")
load("gentoo/2023.01")

if (mode() ~= "spider") then
    prepend_path("MODULEPATH", pathJoin(ccr_easybuild_path, "modules/Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_easybuild_path, "modules", arch, "Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_banalbuild_path, "modules/Core"))
    prepend_path("MODULEPATH", pathJoin(ccr_banalbuild_path, "modules", arch, "Core"))
    local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
    if customBuildPaths ~= nil then
        for customPath in customBuildPaths:split(":") do
            if isDir(pathJoin(customPath, ccr_version, "modules")) then
                prepend_path("MODULEPATH", pathJoin(customPath, ccr_version, "modules/Core"))
                prepend_path("MODULEPATH", pathJoin(customPath, ccr_version, "modules", arch, "Core"))
            end
        end
    end
    if isDir(pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, "modules")) then
        prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, "modules/Core"))
        prepend_path("MODULEPATH", pathJoin(os.getenv("HOME"), ".local/easybuild", ccr_version, "modules", arch, "Core"))
    end
end
