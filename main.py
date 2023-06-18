import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from copy import deepcopy
from desert import isnum
from pfunctions import getTimeSteps
from FGMTableV2 import *
from readOFFiles import *
from scipy.interpolate import interp1d
from tableProperties import FGMtableProperties
from lookup import lookup
from oneDCaseReader import oneDCaseReader
import pickle

FGMtableDict = {}
case1000AdaptiveRoute = "../../Cases/nhep1d/nhep1d1000Adaptive/"
case1000Route         = "../../Cases/nhep1d/nhep1d1000/"
case5000AdaptiveRoute = "../../Cases/nhep1d/nhep1d5000Adaptive/"
case5000Route         = "../../Cases/nhep1d/nhep1d5000/"
case1000DualFuelRoute = "../../Cases/dualFuel1d/DNS1000/"
case4000DualFuelRoute = "../../Cases/dualFuel1d/DNS4000/"


FGMtableDict["route"] = case1000AdaptiveRoute
FGMtableDict["Zrange"] = (0.,1.)
FGMtableDict["fuelList"] = ["C7H16"]
FGMtableDict["gridNumber"] = (301,501)
FGMtableDict["gridPower"] = (2,1)
FGMtableDict["extraLookupFields"] = ["Qdot", "OH","C7H15O2"]
FGMtableDict["PVFields"] = ["N2","CO2","CO","HO2","CH2O","H2O"]
FGMtableDict["PVCoeffs"] = [1.,1.2, 0.9, 2.7, 1.5, 1.2]
FGMtableDict["PVConstant"] = 1.
# FGMtableDict["PVFields"] = ["CO2","CO","HO2","CH2O","H2O"]
# FGMtableDict["PVCoeffs"] = [1.2, 0.9, 2.7, 1.5, 1.2]
# FGMtableDict["PVConstant"] = 0.

obj = FGMtable(FGMtableDict)
obj.Allrun("./","./table_m2a1000/")