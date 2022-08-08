--------------------------------------------------------------------------
-- This code was adopted from and originally written by ComputeCanada:
-- https://github.com/ComputeCanada/software-stack-config/blob/main/lmod/SitePackage_licenses.lua
--
-- Modified for use at CCR. 
--------------------------------------------------------------------------

local function localUserInGroup(group)
	local handle = io.popen("groups 2>/dev/null")
	local grps = handle:read()
	handle:close()
	local found  = false
	for g in string.gmatch(grps, '([^ ]+)') do
		if (g == group)  then
			found = true
			break
		end
	end
	return found
end

local function user_accepted_license(soft,autoaccept)
	require "lfs"
	local posix = require "posix"
	require "io"
	require "os"
	local user = getenv_logged("USER","unknown")
	local home = getenv_logged("HOME",pathJoin("/user",user))
	local license_dir = home .. "/.licenses"
	local license_file = license_dir .. "/" .. soft
	if not (posix.stat(license_dir,"type") == 'directory') then
		lfs.mkdir(license_dir)
	end
	if (posix.stat(license_file,"type") == 'regular') then
		return true
	elseif (autoaccept) then
		local file = io.open(license_file,"w")
		file:close()
		
		local cmd = "logger -t lmod-UA-1.0 -p local0.info User " .. user .. " accepted usage agreement for software " .. soft
 		os.execute(cmd)
		
		return false
	end
	return false
end
local function confirm_acceptance(soft)
	require "io"
	local answer = io.read()
	if (string.lower(answer) == "yes" or string.lower(answer) == "oui") then
		user_accepted_license(soft,true)
		return true
	else 
		return false
	end
	return false
end

function find_and_define_license_file(environment_variable,application)
	require "lfs"
	require "os"
	local mode_s = mode() or nil
	-- unless 
	if (not (mode_s == 'load' or mode_s == 'unload' or mode_s == 'show' or mode_s == 'dependencyCk')) then
		return false
	end
	-- skip the test in these cases
	local fn = myFileName()
	local user = getenv_logged("USER","unknown")
	if ((fn:find("^/cvmfs") == nil and fn:find("^/opt/software") == nil) or user == "ccrbuilder") then
		return true
	end
	local posix = require "posix"
	local license_found = false
	local license_path = ""

	-- if there is already an existing value for the environment variable, never fail
	local existing_value = os.getenv(environment_variable) or nil
	if (existing_value == nil or existing_value == '') then
		license_found = false
	else 
		license_found = true
	end

	-- First, look in /util/software/licenses for a license readable if you are in the right group
	local license_file = pathJoin("/util/software/licenses",application .. ".lic")
	if (posix.stat(license_file,"type") == 'regular') then
		if (io.open(license_file)) then
			license_path = license_file
			prepend_path(environment_variable,license_file)
			license_found = true
		end
	end

	-- Second, look at the user's home for a $HOME/.licenses/<application>.lic
	local home = getenv_logged("HOME",pathJoin("/home",user))
	local license_file = pathJoin(home,".licenses",application .. ".lic")
	if (posix.stat(license_file,"type") == 'regular') then
		license_path = license_file
		prepend_path(environment_variable,license_file)
		license_found = true
	end

	return license_found, license_path
end

function validate_license(t)
	require "io"
	local academic_autoaccept_message = [[
============================================================================================
The software listed above is available for academic usage only. By continuing, you 
accept that you will not use the software for commercial or non-academic purposes. 
============================================================================================
	]]
	local non_commercial_autoaccept_message = [[
============================================================================================
The software listed above is available for non-commercial usage only. By continuing, you 
accept that you will not use the software for commercial purposes. 
============================================================================================
	]]
	local nvidia_autoaccept_message = [[
============================================================================================
The NVidia software listed above is subject to the terms of the NVidia Software
License Agreement, which can be obtained via http://developer.nvidia.com.
By continuing, you accept to be bound by the terms of that license.
============================================================================================
	]]
	local academic_license_message = [[
============================================================================================
Using this software requires you to accept a license on the software website. 
Please confirm that you registered on the website below (yes/no).
============================================================================================
	]]
	local academic_license_message_autoaccept = [[
============================================================================================
Using this software requires you to accept a license on the software website. 
Please ensure that you register on the website below.
============================================================================================
	]]
	local posix_group_message = [[
============================================================================================
Using this software requires you to have access to a license. If you do, please write to
us at ccr-help@buffalo.edu so that we can enable access for you.
============================================================================================
	]]
	local not_accepted_message = [[

============================================================================================
Please answer "yes" to accept.
============================================================================================
	]]
	-- The names in these lists can be full name + version or just the name
	local licenseT = {
		[ { "matlab" } ] = "academic_autoaccept",
		[ { "fsl" } ] = "academic_autoaccept",
		[ { "intel", "signalp", "tmhmm", "rnammer" } ] = "noncommercial_autoaccept",
		[ { "cudnn" } ] = "nvidia_autoaccept",
		[ { "namd", "vmd", "rosetta", "gatk", "gatk-queue", "motioncor2", "pwrf"} ] = "academic_license",
		[ { "namd", "namd-mpi", "namd-verbs", "namd-multicore", "namd-verbs-smp" } ] = "academic_license_autoaccept",
	}
	local groupT = {
		[ "gaussian" ] = "gaussian",
		[ "vasp/4.6" ] = "vasp4",
		[ "vasp/5.4.1" ] = "vasp5",
		[ "imagenet" ] = "imagenet-optin",
		[ "voxceleb"] = "voxceleb-optin",
	}
	local posix_group_messageT = {
		[ { "gaussian" } ] = [[

============================================================================================
Using Gaussian requires you to agree to the following license terms:
 1) I am not a member of a research group developing software competitive to Gaussian.
 2) I will not copy the Gaussian software, nor make it available to anyone else.
 3) I will properly acknowledge Gaussian Inc. and CCR in publications.
 4) I will notify CCR of any change in the above acknowledgement.

If you do, please send an email with a copy of those conditions, saying that you agree to
them at ccr-help@buffalo.edu. We will then be able to grant you access to Gaussian.
============================================================================================
		]],
	}
	local licenseURLT = {
		[ "namd" ] = "http://www.ks.uiuc.edu/Research/namd/license.html",
		[ "vmd" ] = "http://www.ks.uiuc.edu/Research/vmd/current/LICENSE.html",
		[ "gatk" ] = "https://software.broadinstitute.org/gatk/download/licensing.php",
	}
	-- environment variable to define
	local auto_find_environment_variableT = {
--		[ "matlab" ] = "MLM_LICENSE_FILE",
	}
	-- message to display when a license is not found
	local auto_find_messageT = {
--		[ "matlab" ] = [[ test ]]
	}

	local fn = myFileName()
	-- skip tests for modules that are not on /cvmfs
	local user = getenv_logged("USER","unknown")
	if ((fn:find("^/cvmfs") == nil and fn:find("^/opt/software") == nil) or user == "ccrbuilder") then
		return true, nil
	end
	for k,v in pairs(licenseT) do
     		------------------------------------------------------------
		-- Look for fullName first otherwise sn
		local name = ""
		if (has_value(k,myModuleFullName())) then
			name = myModuleFullName()
		elseif (has_value(k,myModuleName())) then
			name = myModuleName()
		end
		
     		if (has_value(k,name)) then
			if (v == "academic_autoaccept") then
				if (not user_accepted_license(name,true)) then
					LmodMessage(myModuleFullName() .. ":")
					LmodMessage(academic_autoaccept_message)
				end
			end
			if (v == "noncommercial_autoaccept") then
				if (not user_accepted_license(name,true)) then
					LmodMessage(myModuleFullName() .. ":")
					LmodMessage(non_commercial_autoaccept_message)
				end
			end
			if (v == "nvidia_autoaccept") then
				if (not user_accepted_license(name,true)) then
					LmodMessage(myModuleFullName() .. ":")
					LmodMessage(nvidia_autoaccept_message)
				end
			end
			if (v == "academic_license") then
				if (not user_accepted_license(name,false)) then
					LmodMessage(myModuleFullName() .. ":")
					LmodMessage(academic_license_message)
					LmodMessage(licenseURLT[name])
					if (not confirm_acceptance(name)) then
						log_module_load(t,false)
						LmodError(not_accepted_message)
					end
				end
			end
			if (v == "academic_license_autoaccept") then
				if (not user_accepted_license(name,true)) then
					LmodMessage(myModuleFullName() .. ":")
					LmodMessage(academic_license_message_autoaccept)
					LmodMessage(licenseURLT[name])
				end
			end
			if (v == "posix_group") then
				if (not localUserInGroup(groupT[name])) then
					log_module_load(t,false)
					local message_found = false
					for k2,v2 in pairs(posix_group_messageT) do
						if (has_value(k2,name)) then
							LmodError(v2)
							message_found = true
						end
					end
					if (not message_found) then
						LmodError(posix_group_message)
					end
				end
			end
			if (v == "auto_find_license") then
				if (not find_and_define_license_file(auto_find_environment_variableT[name],name)) then
					log_module_load(t,false)
					LmodError(auto_find_messageT[name])
				end
			end
		end
	end
end
sandbox_registration{ find_and_define_license_file = find_and_define_license_file }

