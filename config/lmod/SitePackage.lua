--------------------------------------------------------------------------
-- This code was adopted from and originally written by ComputeCanada:
-- https://github.com/ComputeCanada/software-stack-config/blob/main/lmod/SitePackage.lua
--
-- Modified for use at CCR. 
--------------------------------------------------------------------------

--------------------------------------------------------------------------
-- This is a placeholder for site specific functions.
-- @module SitePackage

require("strict")

--------------------------------------------------------------------------------
-- Anything in this file will automatically be loaded everytime the Lmod command
-- is run.  Here are two suggestions on how to use your SitePackage.lua file
--
-- a) Install Lmod normally and then overwrite your SitePackage.lua file over
--    this one in the install directory.

-- b) Create a file named "SitePackage.lua" in a different directory separate
--    from the Lmod installed directory.  Then you should modify
--    your modules.sh and modules.csh (or however you initialize the "module" command)
--    with:
--
--       (for bash, zsh, etc)
--       export LMOD_PACKAGE_PATH=/path/to/the/Site/Directory
--
--       (for csh)
--       setenv LMOD_PACKAGE_PATH /path/to/the/Site/Directory
--
--    A "SitePackage.lua" in that directory will override the one in the Lmod
--    install directory.
--
-----------------------------------------------------------------------------
-- You should check to see that Lmod finds your SitePackage.lua.  If you do:
--
--    $ module --config
--
-- and it reports:
--
--    Modules based on Lua: Version X.Y.Z  3016-02-05 16:31
--        by Robert McLay mclay@tacc.utexas.edu
--
--    Description                      Value
--    -----------                      -----
--    ...
--    Site Pkg location                standard
--
-- Then you haven't set things up correctly.
-----------------------------------------------------------------------------
--  Any function here that is called by a module file must be registered with
--  the sandbox.  For example you have following functions in your
--  SitePackage.lua file:
--
--      function sam()
--      end
--
--      function bill()
--      end
--
--  Then you have to add any functions defined here that you wish to call inside
--  a modulefile with the sandbox by doing:
--      sandbox_registration{ sam = sam, bill = bill}

------------------------------------------------------------------------
-- DO NOT FORGET TO USE CURLY BRACES "{}" and NOT PARENS "()"!!!!
------------------------------------------------------------------------

--  As an example suppose you want to require that users of a particular package must
--  be in a special group.  You can write this function here and use it in any
--  modulefile:
--
--
--     function module_requires_group(group)
--        local grps   = capture("groups")
--        local found  = false
--        local userId = capture("id -u")
--        local isRoot = tonumber(userId) == 0
--        for g in grps:split("[ \n]") do
--           if (g == group or isRoot)  then
--              found = true
--              break
--           end
--        end
--        return found
--     end
--
--     sandbox_registration{ ['required_group'] = module_requires_group }
--
--
--  Then in any module file you can have:
--
--
--     -------------------------
--     foo/1.0.lua:
--     -------------------------
--
--     local err_message="To use this module you must be in a particular group\n" ..
--                       "Please contact foo@my.supercomputer.center to join\n"
--
--     local found = required_group("G123456")
--
--     if (not found) then
--        LmodError(err_message)
--     end
--
--     prepend_path("PATH","/path/to/Foo/Bin")
--
--  Note that here I have used the name "required_group" in the modulefile and named the
--  function as "module_requires_group".  The key is the name used in the modulefile and
--  the right is what the function is called in SitePackage.lua.  The names can be the
--  same.
--------------------------------------------------------------------------

function dofile (filename)
    local f = assert(loadfile(filename))
    return f()
end

local lmod_package_path = os.getenv("LMOD_PACKAGE_PATH")
dofile(pathJoin(lmod_package_path,"SitePackage_logging.lua"))
dofile(pathJoin(lmod_package_path,"SitePackage_licenses.lua"))
dofile(pathJoin(lmod_package_path,"SitePackage_families.lua"))
dofile(pathJoin(lmod_package_path,"SitePackage_properties.lua"))
dofile(pathJoin(lmod_package_path,"SitePackage_hidden.lua"))

sandbox_registration{ loadfile = loadfile, assert = assert, loaded_modules = loaded_modules, serializeTbl = serializeTbl }

require("strict")
require("string_utils")
local hook    = require("Hook")
local uname   = require("posix").uname
local cosmic  = require("Cosmic"):singleton()
local syshost = cosmic:value("LMOD_SYSHOST")
local time = os.time
local date = os.date

function has_value(tab, val)
    for index, value in ipairs(tab) do
        if value == val then
            return true
        end
    end
    return false
end

local function unload_hook(t)
        set_family(t)
end

local function visible_hook(modT)
        set_hidden(modT)
end

local function load_hook(t)
    local valid = validate_license(t)
    set_props(t)
    set_family(t)
    log_module_load(t,true)
end

local function spider_hook(t)
        set_props(t)
end

hook.register("unload",         unload_hook)
hook.register("load",           load_hook)
hook.register("load_spider",    spider_hook)
hook.register("isVisibleHook",  visible_hook)

--------------------------------------------------------------------------
--  This code implementes CCR's custom grouped labels for module avail
--  See: https://lmod.readthedocs.io/en/latest/200_avail_custom.html?highlight=grouped
--------------------------------------------------------------------------
local ccr_init = os.getenv("CCR_INIT_DIR")
local mapT =
{
   grouped = {
      ['/modules/Core']     = "Core modules",
      [ccr_init .. '/modulefiles$'] = "Core modules",
      ['/srv/software%-layer/config/modulefiles$'] = "Core modules",
      ['/util/software/config%-dev/modulefiles$'] = "Core modules",
   },
}

local baseLabelMap = {}
for _, microArch in pairs({'avx512', 'avx2', 'x86%-64%-v4', 'x86%-64%-v3', 'neoverse%-v2'}) do
    baseLabelMap['/modules/'..microArch.. '/Core'] = 'Core modules'
    baseLabelMap['/modules/'..microArch.. '/Compiler'] = 'Compiler-dependent ' .. microArch:gsub('%%', '') .. ' modules'
    baseLabelMap['/modules/'..microArch.. '/MPI'] = 'MPI-dependent ' .. microArch:gsub('%%', '') .. ' modules'
end

for pat, label in pairs(baseLabelMap) do
    mapT['grouped']['/cvmfs/.*'..pat] = label
    mapT['grouped'][os.getenv('HOME')..'.*'..pat] = 'Your personal '..label
end


function avail_hook(t)
   local availStyle = masterTbl().availStyle
   local styleT     = mapT[availStyle]
   if (not availStyle or availStyle == "system" or styleT == nil) then
       return
   end
   local customBuildPaths = os.getenv("CCR_CUSTOM_BUILD_PATHS") or nil
   if customBuildPaths ~= nil then
       for customPath in customBuildPaths:split(":") do
           for pat, label in pairs(baseLabelMap) do
              styleT[customPath..'.*'..pat] = customPath..' '..label
           end
       end
   end
   for k,v in pairs(t) do
       for pat,label in pairs(styleT) do
          if (k:find(pat)) then
             t[k] = label
             break
          end
       end
   end
end

hook.register("avail",avail_hook)
