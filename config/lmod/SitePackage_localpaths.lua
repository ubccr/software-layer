require("serializeTbl")
require("string_utils")

function set_local_paths(t)
	
	local localModulePaths = os.getenv("CCR_LOCAL_MODULEPATHS") or nil
	if localModulePaths == nil then
		return
	end


	local moduleNamesToCheck = { "openmpi", "intelmpi", "gcc", "intel", "pgi", "cuda" }
	local myModuleName = myModuleName()

	if has_value(moduleNamesToCheck, myModuleName) then
		local arch = os.getenv("CCR_ARCH")
		local myModuleFullName = myModuleFullName()
		local myFileName = myFileName()

		-- get module version with two dots only
		local myModuleVersion = myModuleVersion()
		local myModuleVersionTwoDigits = string.gsub(myModuleVersion, ".[0-9]*$", "")
		local myModuleVersionOneDigit = string.gsub(myModuleVersionTwoDigits, ".[0-9]*$", "")
		myModuleVersionOneDigit = tonumber(myModuleVersionOneDigit) or 0

		local rootEasyBuildModulePath = os.getenv("CCR_SOFTWARE_PATH") .. "/modules"
		local rootModulePath = rootEasyBuildModulePath
		local relativeFileName = string.gsub(myFileName, rootModulePath, "")
		-- from the module filename, remove the <name>/<version>.lua
		local relativeModulePaths = string.gsub(relativeFileName, myModuleFullName .. ".lua", "")
--			LmodWarning("myModuleName:" .. myModuleName)
--			LmodWarning("initial:" .. relativeModulePaths)

		local subPath = myModuleName .. myModuleVersionTwoDigits

		if myModuleName == "openmpi" or myModuleName == "intelmpi" or myModuleName == "impi" then
			-- build the module path by changing Compiler or CUDA by MPI 
			relativeModulePaths = string.gsub(relativeModulePaths, "/Compiler/", "/MPI/")
			relativeModulePaths = string.gsub(relativeModulePaths, "/CUDA/", "/MPI/")
		elseif myModuleName == "gcc" or myModuleName == "intel" or myModuleName == "pgi" then
			-- build the module path by changing Core by Compiler
			relativeModulePaths = string.gsub(relativeModulePaths, "/Core/", "/" .. arch .. "/Compiler/")
			relativeModulePaths = string.gsub(relativeModulePaths, "/Core%-sse3/", "/" .. arch .. "/Compiler/")
			relativeModulePaths = string.gsub(relativeModulePaths, "/Core%-avx/", "/" .. arch .. "/Compiler/")
			relativeModulePaths = string.gsub(relativeModulePaths, "/Core%-avx2/", "/" .. arch .. "/Compiler/")
			relativeModulePaths = string.gsub(relativeModulePaths, "/Core%-avx512/", "/" .. arch .. "/Compiler/")
--				LmodWarning("replaced:" .. relativeModulePaths)
		elseif myModuleName == "cuda" then
			-- build the module path by changing Compiler for CUDA
			relativeModulePaths = string.gsub(relativeModulePaths, "/Compiler/", "/CUDA/")
		end
--			LmodWarning("after_replacement:" .. relativeModulePaths)

		-- intelmpi is a corner case in which we don't use the same convention
		if myModuleName == "intelmpi" then
			subPath = "impi" .. myModuleVersionTwoDigits
		end
		-- gcc >= 8, intel >= 2019, openmpi >= 4 use a single version for directories
		if myModuleName == "gcc" and myModuleVersionOneDigit >= 8 then
			subPath = myModuleName .. myModuleVersionOneDigit
		end
		if myModuleName == "intel" and myModuleVersionOneDigit >= 2019 then
			subPath = myModuleName .. myModuleVersionOneDigit
		end
		if myModuleName == "openmpi" and myModuleVersionOneDigit >= 4 then
			subPath = myModuleName .. myModuleVersionOneDigit
		end
		--LmodWarning(subPath)
		--LmodWarning(relativeModulePaths)
		-- and adding the subPath
		relativeModulePaths = pathJoin(relativeModulePaths, subPath)

		for localModulePathRoot in localModulePaths:split(":") do
			for relativeModulePath in relativeModulePaths:split(":") do
				local localModulePath = pathJoin(localModulePathRoot, relativeModulePath)
				--LmodWarning(localModulePath)
				--LmodWarning(myModuleFullName .. ":" .. localModulePath)
				if isDir(localModulePath) then
					prepend_path("MODULEPATH", localModulePath)
				end
			end
		end
	end
end

