-- CCR default versions
if os.getenv("CCR_CPU_FAMILY") == "aarch64" then
    module_version("ccrsoft/2024.04","default")
    hide_version("ccrsoft/2023.01")
    hide_version("ccrsoft/legacy")
else
    module_version("ccrsoft/2023.01","default")
    hide_version("ccrsoft/2024.04")
end
module_version("easybuild/4.9.1","default")

-- shortcuts
module_version("gcc/13.2.0","13")

-- hidden modules
