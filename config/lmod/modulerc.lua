-- CCR default versions
module_version("gcc/9.3.0","default")
module_version("gcccore/9.3.0","default")
module_version("intel/2020a","default")

-- shortcuts
module_version("gcc/9.3.0","9")
module_version("gcc/10.3.0","10")
module_version("gcc/11.2.0","11")
module_version("intel/2020a","2020")

-- hidden modules
hide_version("gcccore/9.3.0")
hide_version("gcccore/10.3.0")
hide_version("gcccore/11.2.0")
hide_version("iccifort/2020.1.217")
