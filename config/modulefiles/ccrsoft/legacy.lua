help([==[

Description
===========
CCR Legacy Software release.


More information
================
 - Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/
]==])

whatis([==[Description: CCR Legacy Software release]==])
whatis([==[Homepage: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])
whatis([==[URL: https://docs.ccr.buffalo.edu/en/latest/software/releases/]==])

add_property(   "lmod", "sticky")
require("os")
require("SitePackage")
load("ccrenv")

setenv("CCR_VERSION", "legacy")
local arch = os.getenv("CCR_ARCH") or ""
setenv("CCR_PREFIX", "")
setenv("CCR_EASYBUILD_PATH", "")
setenv("CCR_BANALBUILD_PATH", "")

if not arch or arch == "" then
    arch = get_highest_supported_architecture()
    setenv("CCR_ARCH", arch)
end

if (mode() ~= "spider") then
    prepend_path("MODULEPATH", "/util/common/modulefiles/Core")
    prepend_path("MODULEPATH", "/util/academic/modulefiles/Core")
end

if mode() == "load" then
io.stderr:write([==[***************************** WARNING *********************************************
You're loading very old software that is no longer supported.  This software will be removed from CCR
during the June 2024 downtime.  Please update your workflow to utilize CCR's latest software release
*****************************************************************************************
]==])
end
