#
# Honeybee: A Plugin for Environmental Analysis (GPL) started by Mostapha Sadeghipour Roudsari
# 
# This file is part of Honeybee.
# 
# Copyright (c) 2013-2018, Anton Szilasi <ajszilas@gmail.com> 
# Honeybee is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# Honeybee is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Honeybee; If not, see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>



"""
Provided by Honeybee 0.0.63

Use this component to add Energy Plus Photovoltaic generators to a Honeybee Surface. Each surface can only have one Photovoltaic generator. While each PV generator is made up of one or several PV modules. 
-
At present only Photovoltaic generators with Simple Photovoltaic performance objects are supported.
-
For each Photovoltaic generator there must be a inverter for power to be produced, if several photovoltaic generators are modelled in the same generatorsystem (Connected to the generationsystem component) these generators must have the same inverter.

For more information about Photovolatic generators please see: 
-
http://bigladdersoftware.com/epx/docs/8-2/input-output-reference/group-electric-load-center.html#photovoltaic-generators

-
Provided by Honeybee 0.0.63

    Args:
        _HBSurfaces: A Honeybee/context surface or a list of Honeybee/context surfaces to which one Photovolatic generator will be mounted on each surface.
        _name_: An optional input, a name or a list of names of PV generators which correspond sequentially to the Honeybee surfaces in _HBSurfaces. Without this input PV generators will be assigned default names.
        _SASolarCells: A float or a list of floats that sequentially correspond to what percentage of each Honeybee surface in  _HBSurfaces are covered with Photovoltaics.  e.g the first float corresponds to the first Honeybee surface. If only one float is given this value will be used for all other PV generators.
        _cellsEfficiency: A float or a list of floats that sequentially detail the efficiency of the Photovoltaic generator cells on each Honeybee surface in _HBSurfaces as a fraction. e.g the first float corresponds to the first Honeybee surface. If only one float is given this value will be used for all other PV generators.
        _NoParallel: A integer or a list of integers that sequentially correspond to each Honeybee surface in _HBSurfaces. These integers define the series-wired strings of PV modules that are in parallel to form the PV generator on each Honeybee surface. The product of this field and the next field will equal the total number of modules in the PV generator on each Honeybee surface. If only one integer is given this value will be used for all other PV generators.
        _Noseries: A integer or a list of integers that sequentially correspond to each Honeybee surface in _HBSurfaces.  These integers define the number of modules wired in series (on each string) to form the PV generator on each Honeybee surface in _HBSurfaces. The product of this field and the previous field will equal the total number of modules in the PV generator on each Honeybee surface. If only one integer is given this value will be used for all other PV generators.
        costPVgen_: A float or a list of floats that sequentially correspond to each Honeybee surface in _HBSurfaces. The float is the cost of each PV module in US dollars (Other currencies will be available in the future). The cost of the PV generator will be the cost of the module multiplied by the number of modules in parallel and series (number of modules as a generator is made up of modules). If only one float is given this value will be used for all other PV generators. Default is set to $0.
        _powerOutput: A float or a list of floats that sequentially correspond to each Honeybee surface in _HBSurfaces. The float is the power output of each PV module in watts. The power output of the PV generator will be the power output of the module multiplied by the number of modules in parallel and series (number of modules as a generator is made up of modules). If only one float is given this value will be used for all other PV generators.
        _PVInverter: The inverter servicing all the PV generators in this component - to assign an inverter connect the HB_inverter here from the Honeybee inverter component
        sandiaMode_: Input just ONE Sandria data set as a panel here. Examples can be seen in C:\EnergyPlusV8-4-0\MacroDataSet\SandiaPVdata
            
    Returns:
        PV_HBSurfaces: The Honeybee/context surfaces that have been modified by this component - these surfaces now contain PV generators to run in an EnergyPlus simulation. To do so you need to add them to a Honeybee generation system first - connect them to the PV_HBSurfaces input of a Honeybee_generationsystem component.
        
"""

ghenv.Component.Name = "Honeybee_Generator_PV"
ghenv.Component.NickName = 'PVgen'
ghenv.Component.Message = 'VER 0.0.63\nSEP_11_2018'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "09 | Energy | HVACSystems"
#compatibleHBVersion = VER 0.0.56\nNOV_04_2016
#compatibleLBVersion = VER 0.0.59\nFEB_01_2015
try: ghenv.Component.AdditionalHelpFromDocStrings = "0"
except: pass

import scriptcontext as sc
import uuid
import Grasshopper.Kernel as gh
import itertools
import Grasshopper
import collections
import re
import Rhino

hb_hive = sc.sticky["honeybee_Hive"]() # Creating an instance of hb_hive here
PV_gen = sc.sticky["PVgen"] # Linked to class PV_gen in honeybee honeybee 
hb_hivegen = sc.sticky["honeybee_generationHive"]() # Creating an instance of the hb_hivegen here 

readmedatatree = Grasshopper.DataTree[object]()

def checktheinputs(_name_,_HBSurfaces,_cellsEfficiency,_NoParallel,_Noseries):

    """This function checks all the inputs of the component to ensure that the component is stopped if there is anything wrong with the inputs ie the 
    inputs will produce serious errors in the execution of this component.
        
        Args:
            The arguements seen in the function definition are the same as the arguements on the panel.
            
        Returns:
            If there are any issues with the inputs this function will return -1 and the component will stop"""
          
    # Check if the Honeybee hive is on the sticky
    
    if not sc.sticky.has_key("honeybee_release") or not sc.sticky.has_key("honeybee_ScheduleLib"):
        print "You should first let the Honeybee fly..."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "You should first let the Honeybee fly...")

        return -1

    try:
        if not sc.sticky['honeybee_release'].isCompatible(ghenv.Component): return -1
        if sc.sticky['honeybee_release'].isInputMissing(ghenv.Component): return -1
    except:
        
        warning = "You need a newer version of Honeybee to use this compoent." + \
        "Use updateHoneybee component to update userObjects.\n" + \
        "If you have already updated userObjects drag Honeybee_Honeybee component " + \
        "into canvas and try again."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, warning)
        return -1  

    # Simple check for sandia to be expanded upon
        
    # Check that Honeybee Zones are connected
   
    if (_PVInverter == []) or (_PVInverter == None):
        
        print " Please connect an inverter to _PVInverter"
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "Please connect an inverter to _PVInverter")
        return -1
        
    if len(_PVInverter) != 1:
        
        print " There can only be one inverter for each PV generator please connect only one inverter!"
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "There can only be one inverter for each PV generator please connect only one inverter!")
        return -1
        
    
    if (_HBSurfaces == []) or (_HBSurfaces[0] == None) :
        print "PV generators must be mounted on at least one Honeybee surface or context surface please connect a Honeybee surface to _HBSurfaces!"
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "PV generators must be mounted on at least one Honeybee surface or context surface please connect a Honeybee surface to _HBSurfaces!")
        return -1
       
    if (_cellsEfficiency == []) or (_cellsEfficiency[0]) == None:
        print "_cellsEfficiency must contain one or a number of decimal floats!"
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "_cellsEfficiency must contain one or a number of decimal floats!")
        return -1
        
        
    for cell_n in _cellsEfficiency:
            
        if (cell_n >1) or (cell_n < 0):
            
            print "All values of _cellsEfficiency must be between 1 and zero as it is a efficiency!"
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, "All values of _cellsEfficiency must be between 1 and zero as it is a efficiency!")
            return -1
            
    for PVgencount in range(len(_HBSurfaces)):
        
        try:
            _HBSurfaces[PVgencount]
        except IndexError:
            warnMsg= "Every PV generator must have a corresponding surface connected through the field _HBSurfaces! "
            print warnMsg
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warnMsg)
            return -1 
    
    if (_powerOutputPerModule == []) or (_powerOutputPerModule[0]) == None:
        print "The power output of the module/s must be specified!"
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "The power output of the module must be specified!")
        return -1
        
        
def returnmodename(mode):
    """ This function converts _integrationMode from an int on the panel to a string for the Generator:Photovoltaic Heat Transfer integration mode
    so it is an enum function.
    """
    if mode == 1:
        return "Decoupled"
    if mode ==2:
        return "DecoupledUllebergDynamic"
    if mode ==3:
        return "IntegratedSurfaceOutsideFace"
    if mode==4:
        return "IntegratedTranspiredCollector"
    if mode==5:
        return "IntegratedExteriorVentedCavity"
    if mode==6:
        return "PhotovoltaicThermalSolarCollector"


def main(_name_,_HBSurfaces,_cellsEfficiency,_NoParallel,_Noseries,_powerOutput,PVinverter):
 
    """ This function is the heart of this component it takes all the component arguments and writes one PV generator onto each Honeybee surface connected to this component
 
     Args:
            The arguements seen in the function definition are the same as the arguements on the panel.
                
        Returns:
            The properties of the PV generators connected to this component these properties are then written to an IDF file in Honeybee_ Run Energy Simulation component.
    """
    
    HBSurfacesfromhive = hb_hive.callFromHoneybeeHive(_HBSurfaces) # Call Honeybee surfaces from hive
    
    PVgencount = 0
    
    # CHECK that the same surfaces are not having PV generators added to them twice. If they are stop the component.
    
    class myDict(dict):

        def __init__(self):
            self = dict()
    
        def add(self, key, value):
            self[key] = value
    
    HBsurfaces = myDict()
    
    for HBsurface in HBSurfacesfromhive:
        
        # In order of Honeybee surface, Honeybee surface ID and Brep which corresponds to that Honeybee surface
        
        HBsurfaces.add(HBsurface,HBsurface.ID)
        
    if len(HBsurfaces.values()) != len(set(HBsurfaces.values())):
        
        # Identify duplicateIDs
        
        duplicateIDs = collections.Counter([item for item in HBsurfaces.values()]).keys()
        
        surfaceCount = 0
        
        for surface,surfaceID in HBsurfaces.items():
            
            if surfaceID in duplicateIDs:
                
                warn = "Into the input _HBSurfaces you have input the same surface " + HBsurface.name + " twice. Use Geometry preview to make sure \n"+\
                "that the same surfaces are not being input several times. This component will not run until this is fixed."
                
                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Error, warn)
                
                # Draw a preview of the geometry so the user can identify it.
                
                preview = Grasshopper.Kernel.GH_PreviewUtil()
                
                preview.AddBrep(_HBSurfaces[surfaceCount])
                
                surfaceCount =+ 1
                
                return

    try:
    
        for name,surface,celleff,parallel,series,powerout,costPVgen in itertools.izip_longest(_name_,HBSurfacesfromhive,_cellsEfficiency,_NoParallel,_Noseries,_powerOutputPerModule, costPVgen_): 
    
            surface.containsPVgen = True # Set this it true so the surface can be identified in run and write IDF component
            
            surface.PVgenlist = [] # Set the PVgenlist of each surface back to empty otherwise PVgen objects will accumulate on each run
            
            
            namePVperform = "PVperformance" + str(PVgencount)+ " " + str(surface.name) # Create a name for the PVperformance object for each PV generator - this is always created by automatically here not by the user
    
            # Raise some warnings for the following circumstances 
            
            centerPt, normalVector = surface.getSrfCenPtandNormalAlternate()
            
            if normalVector[2] == -1:
                
                w = gh.GH_RuntimeMessageLevel.Warning
                
                warn = "Are you sure that you want to mount PV generators on " + str(surface.name) +" \n"+\
                "the surface normal of this surface is facing down!"
                
                ghenv.Component.AddRuntimeMessage(w, warn)
                
            if surface.type == 2.5:
                
                w = gh.GH_RuntimeMessageLevel.Warning
                
                warn = str(surface.name) +" is a on-ground slab you probably don't want to mount PV panels on it \n"+\
                "but we will go ahead and do it anyway."
                
                ghenv.Component.AddRuntimeMessage(w, warn)
    
            if surface.type == 2.25:
                
                w = gh.GH_RuntimeMessageLevel.Warning
                
                warn = str(surface.name) +" is a underground slab you probably don't want to mount PV panels on it \n"+\
                "but we will go ahead and do it anyway."
                
                ghenv.Component.AddRuntimeMessage(w, warn)
    
                
            if surface.type == 0.5:
            
                w = gh.GH_RuntimeMessageLevel.Warning
                
                warn = str(surface.name) +" is a underground wall you probably don't want to mount PV panels on it \n"+\
                "but we will go ahead and do it anyway."
                
                ghenv.Component.AddRuntimeMessage(w, warn)
            
            try:
    
                name = _name_[PVgencount]
                message0 = _name_[PVgencount] + " is mounted on Honeybee surface "+ str(surface.name)
    
            except IndexError:
                
                name = "PVgenerator" + str(PVgencount)
                message0 = "For this generator no name has been given so a default name of PVgenerator" + str(PVgencount) + " has been assigned. This generator is mounted on Honeybee surface " + str(surface.name) # If no name given for a PV generator assign one.
            
            try:
    
                _cellsEfficiency[PVgencount]
                
                message4 = "The number of PV modules in parallel is "+ str(parallel)
            
            except IndexError:
                
                parallel = _cellsEfficiency[0]
                
                message4 = "The number of PV modules in parallel is "+ str(parallel) 
            
            
            
            try:
    
                _NoParallel[PVgencount]
                
                message4 = "The number of PV modules in parallel is "+ str(parallel)
            
            except IndexError:
                
                parallel = _NoParallel[0]
                
                message4 = "The number of PV modules in parallel is "+ str(parallel) 
            
    
            try:
    
                _Noseries[PVgencount]
                message5 = "The number of PV modules in series is " + str(series)
    
                
            except IndexError:
                
                series = _Noseries[0]
                message5 = "The number of PV modules in series is " + str(series)
                
                
            message6 = "So " + name + " is made up of "+ str(series*parallel) + " PV modules"
                
            try:
                _powerOutputPerModule[PVgencount]
    
                message8 = "The power output per PV module is " + str(powerout) + " W \n " +\
                "Therefore the total power output of "+ name+" is " + str(powerout*float(parallel*series)) + " W "
    
                
            except IndexError:
                
                powerout = _powerOutputPerModule[0]
                message8 = "The power output per PV module is " + str(powerout) + " W \n " +\
                "Therefore the total power output of "+ name+ " is " + str(powerout*float(parallel*series)) + " W "
            
            # The surface area of the surface that the PV panels cover are calculated from this equation.
            
            SA_solarcell = (powerout*parallel*series)/(1000*surface.getArea()*celleff)
            
            if (SA_solarcell > 0.85) and (SA_solarcell < 1):
                
                warn = "According to your inputs solar panels cover more than 85% of the surface area of the Honeybee surface "+ surface.name+ "\n"+\
                "Are you sure that the power rating and the number of modules on this surface are correct? \n "+\
                "This value is calculated from the total power output of each PV generator (The sum of each PV module in that generator) divided by the surface area of the surface they are mounted on. \n"+ \
                "Don't worry though this component will still run!"
                w = gh.GH_RuntimeMessageLevel.Warning
                ghenv.Component.AddRuntimeMessage(w, warn)
                
                
            if SA_solarcell >= 1:
                
                warn = "Error! According to your inputs solar panels cover more than 100% of the surface area of the Honeybee surface " + surface.name+"\n"+\
                "Are you sure that the power rating and the number of modules on each surface is correct and that units are in meters? \n "+\
                "This value is calculated from the total power output of each PV generator (The sum of each PV module in that generator) divided by the surface area of the surface they are mounted on."
                "This component will not run until the surface area is less than 100%."
                w = gh.GH_RuntimeMessageLevel.Error
                ghenv.Component.AddRuntimeMessage(w, warn)
                
                return

            if SA_solarcell < 0.025:
                
                warn = "Warning! According to your inputs solar panels cover less than 2.5% of the surface area of " + surface.name+"\n"+\
                "Are you sure that the power rating and the number of modules on each surface is correct? \n "+\
                "This value is calculated from the total power output of each PV generator (The sum of each PV module in that generator) divided by the surface area of the surface they are mounted on."
                "This component will not run until the surface area is less than 100%."
                w = gh.GH_RuntimeMessageLevel.Warning
                ghenv.Component.AddRuntimeMessage(w, warn)
                
            units = sc.doc.ModelUnitSystem
            if units != Rhino.UnitSystem.Meters:
                
                warn = "You must use meters as your unit system to work with the PV component!"
                w = gh.GH_RuntimeMessageLevel.Error
                ghenv.Component.AddRuntimeMessage(w, warn)
                
                
            message1 = "According to the data you entered it is calculated that the modules of this PV generator cover roughly "+str(round(SA_solarcell*100,2))+ " % of the surface area of this surface"
            
                
            surface.PVgenlist.append(PV_gen(name,surface,parallel,series,powerout,SA_solarcell,celleff,costPVgen))
                
            # Assign the inverter to each PVgenerator.
            
            for PVgen in surface.PVgenlist:
                
                PVgen.inverter = PVinverter
            
            message = message0 +" \n "+ name + " has the following properties: "+"\n "+message1+"\n "+message4+"\n "+message5+"\n "+ message6 +"\n "+message8
            
            readmedatatree.Add(message,gh.Data.GH_Path(PVgencount))
                
            PVgencount = PVgencount+1

    except Exception as e:
        
        if str(e) == "unsupported operand type(s) for *: 'float' and 'NoneType'":
            
            # This catches an error when there is a missing member exception ie length of one of inputs is longer than 
            # number of Honeybee surfaces not sure how to just catch missing member exception!
            warn = "The length of a list of inputs into either _name_,_cellsEfficiency \n" + \
                    "_integrationMode,_NoParallel,_Noseries,costPVgen_ or _powerOutput \n" + \
                    "is longer than the number of Honeybee surfaces connected to this component!\n" + \
                    "e.g if you have 2 Honeybee surfaces you cannot have 3 values input into costPVgen_!\n" + \
                    "Please check the inputs and try again!"
        
            #print warn
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warn)
            return -1 
            
        elif str(e) == "'NoneType' object has no attribute 'containsPVgen'":
            
            # This catches an error when there is a missing member exception ie length of one of inputs is longer than 
            # number of Honeybee surfaces not sure how to just catch missing member exception!
            warn = "The length of a list of inputs into either _name_,_cellsEfficiency \n" + \
                    "_integrationMode,_NoParallel,_Noseries,costPVgen_ or _powerOutput \n" + \
                    "is longer than the number of Honeybee surfaces connected to this component!\n" + \
                    "e.g if you have 2 Honeybee surfaces you cannot have 3 values input into costPVgen_!\n" + \
                    "Please check the inputs and try again!"
        
            #print warn
            w = gh.GH_RuntimeMessageLevel.Warning
            ghenv.Component.AddRuntimeMessage(w, warn)
            return -1
        
        else:
            raise
        
    ModifiedHBSurfaces = hb_hive.addToHoneybeeHive(HBSurfacesfromhive, ghenv.Component)
    
    return ModifiedHBSurfaces

# Call the PVinverter from the hive

PVinverter = hb_hivegen.callFromHoneybeeHive(_PVInverter)

if checktheinputs(_name_,_HBSurfaces,_cellsEfficiency,_NoParallel,_Noseries) != -1:

    PV_HBSurfaces = main(_name_,_HBSurfaces,_cellsEfficiency,_NoParallel,_Noseries,_powerOutputPerModule,PVinverter)
    
    readMe = readmedatatree