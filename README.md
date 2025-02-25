# CCR Software Layer

## About

Software at CCR is built using [easybuild](https://docs.easybuild.io/en/latest/) and available via modules using [Lmod](https://lmod.readthedocs.io/en/latest/).  CCR's [standard software environments](https://docs.ccr.buffalo.edu/en/latest/software/releases/) provide a method for users to switch between versions of toolchains, compilers, libraries, and other packages compiled with specific optimizations enabled to take advantage of the various features of each CPU microarchitecture available in CCR's HPC environment.  For more information about using software modules, refer to the [documentation](https://docs.ccr.buffalo.edu/en/latest/software/modules/).


## CCR Software Policy  

Please refer to the [CCR documentation](https://docs.ccr.buffalo.edu/en/latest/policies/software) for information about what software is provided by CCR, instructions for requesting software installations, and details on what restrictions or limitations are enforced.  

## Installing Software Yourself   

CCR users are able to install software themselves in their project and home directories or utilize container environments for custom installations.  For more information, please refer to the Easybuild documentation [here](https://docs.ccr.buffalo.edu/en/latest/software/building/), an Easybuild how-to tutorial [here](https://docs.ccr.buffalo.edu/en/latest/howto/easybuild/), and container documentation [here](https://docs.ccr.buffalo.edu/en/latest/howto/containerization/).  We also have Python-specific documentation [here](https://docs.ccr.buffalo.edu/en/latest/howto/python/).  If you're unsure which method makes the most sense for your workflow, contact [CCR Help](https://docs.ccr.buffalo.edu/en/latest/help/) for guidance.  

## Submitting Software Build Requests and Bug Reports  

**Installation Requests:**  
CCR users should submit build requests for staff to install software using [GitHub issues](https://github.com/ubccr/software-layer/issues).  Before submitting a new request, please search the issues to see if another user has already requested an installation of the software you're interested in. If there is, rather than submitting a new request, please "like" the GitHub issue and comment on it to let us know which research group you're work for.  This helps us to prioritize the build requests. When creating a new issue you should select the `Software Request` template which asks for the following information:
  - Your last name so we can lookup your CCR account (this is a public repo so please don't share your username)  
  - The last name of the faculty member in charge of the research group you're working with  
  - A list of any other research groups that you may know of that are interested in this software  
  - A link to the software website so we can ensure we're building the software you want. There are many packages with the same name for different scientific disiplines!  
  - The preferred version of the software you'd like us to install  
  - Which [CCR software environment](https://docs.ccr.buffalo.edu/en/latest/software/releases/) you'd like the software published to  
  - Any additional information you'd like to share about your request
  
**Please enter a new request for each piece of software you'd like installed.**

**Bug Reports:**  
If you experience an issue with an installed module on CCR's systems, please submit a bug report.  Bug reports should only be submitted for problems with the software installation or the Easybuild system itself.    If you need assistance with using a particular software module, running jobs, or anything else related to CCR's systems, please submit a [help request](https://www.buffalo.edu/ccr/support.html) using our ticketing system.  

## See Also

The config files and scripts in this repo were heavily adopted from [EESSI](https://github.com/EESSI) 
and [Compute Canada](https://github.com/ComputeCanada). You can check out their configs here:

- https://github.com/EESSI/software-layer
- https://github.com/ComputeCanada/easybuild-computecanada-config


## License

The software in this repository is distributed under the terms of the GNU
General Public License v2.0. See the LICENSE file.
