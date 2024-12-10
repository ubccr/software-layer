-- CCR default versions
module_version("ccrsoft/2024.04","default")
module_version("easybuild/4.9.4","default")

-- shortcuts
module_version("gcc/13.2.0","13")

-- hidden modules

if os.getenv("CCR_CPU_FAMILY") == "aarch64" then
    hide_version("ccrsoft/2023.01")
end

hide_version("easybuild/4.9.1")
