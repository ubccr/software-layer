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
io.stderr:write([==[****************WARNING - DANGER - THE SHIP IS GOING DOWN ******************
You're loading really freaking old software and it is being deleted very soon.  Please
update your workflow to bring yourself into this century
*****************************************************************************************
]==])
end
