require("SitePackage")

local ccr_cluster = os.getenv("CCR_CLUSTER") or "ub-hpc"
local arch = os.getenv("CCR_ARCH") or ""
local interconnect = os.getenv("CCR_INTERCONNECT") or ""
local cpu_vendor_id = os.getenv("CCR_CPU_VENDOR_ID") or ""
local ccr_init_dir = os.getenv("CCR_INIT_DIR")

if not arch or arch == "" then
    arch = get_highest_supported_architecture()
end
if not cpu_vendor_id or cpu_vendor_id == "" then
    cpu_vendor_id = get_cpu_vendor_id()
end
if not interconnect or interconnect == "" then
    interconnect = get_interconnect()
end
local cuda_driver_version = os.getenv("CCR_CUDA_DRIVER_VERSION") or ""
if not cuda_driver_version or cuda_driver_version == "" then
    cuda_driver_version = get_installed_cuda_driver_version()
end

assert(loadfile(pathJoin(ccr_init_dir, "modulefiles/gentoo/2022.05.lua.core")))(arch, cpu_vendor_id, interconnect, cuda_driver_version)
