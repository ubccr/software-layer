# -*- lua -*-

-- Possible colors:  black, red, green, yellow, blue, magenta, cyan, and white
propT = {
   lmod = {
      validT = { sticky = 1 },
      displayT = {
         sticky = { short = "(S)",  long = "(S)",   color = "red", doc = "Module is Sticky, requires --force to unload or purge",  },
      },
   },
   type_ = {
      validT = { tools = 1, mpi = 2, script = 3, math = 4, chem = 5, bio = 6, vis = 7, phys = 8, geo = 9, io = 10, ai = 11, os = 12 },
      displayT = {
         ["tools"]     = { short = "(t)",  long = "(tool)",   color = "blue", doc = "Tools for development", },
         ["mpi"]     = { short = "(m)",  long = "(mpi)",   color = "red", doc = "MPI implementations", },
         ["script"]     = { short = "(s)",  long = "(script)",   color = "yellow", doc = "Scripting language", },
         ["math"]     = { short = "(math)",  long = "(math)",   color = "green", doc = "Mathematical libraries", },
         ["chem"]     = { short = "(chem)",  long = "(chem)",   color = "magenta", doc = "Chemistry libraries/apps", },
         ["phys"]     = { short = "(phys)",  long = "(phys)",   color = "cyan", doc = "Physics libraries/apps", },
         ["geo"]     = { short = "(geo)",  long = "(geo)",   color = "cyan", doc = "Geography libraries/apps", },
         ["bio"]     = { short = "(bio)",  long = "(bio)",   color = "red", doc = "Bioinformatic libraries/apps", },
         ["vis"]     = { short = "(vis)",  long = "(vis)",   color = "blue", doc = "Visualisation software", },
         ["io"]     = { short = "(io)",  long = "(io)",   color = "yellow", doc = "Input/output software", },
         ["ai"]     = { short = "(ai)",  long = "(ai)",   color = "yellow", doc = "Artificial intelligence", },
         ["os"]     = { short = "(os)",  long = "(os)",   color = "blue", doc = "Base OS", },
      },
   },
}
