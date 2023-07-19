import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from copy import deepcopy
from functions import is_number, getTimeSteps, isnum
import os

def readOFScalarList(tablename, baseRoute = "./Table_ZChp_301_501_1_1/"):
    filename = baseRoute + tablename
    with open(filename,'r') as myfile:
        startFlag = False
        dimFlag   = False
        data      = []
        dimension = 0
        
        print("Reading {}".format(tablename))
        for line in myfile.readlines():
            line = line.strip("\n")
            if (line != ""):
                if ((not startFlag) and (line in filename)):
                    startFlag = True
                
                # start reading ,first initialize the dimension, then append the data
                if (startFlag and isnum(line)):
                    if (not dimFlag):
                        dimension = int(line)
                        dimFlag = True
                    else:
                        data.append(float(line))
                
        # perform size check
        if (np.size(data) == dimension):
            pass
            #print("Passing dimension check for field {} with size of the data = {}".format(filename,np.size(data)))    
    fieldDict = {}
    fieldDict["dimension"] = dimension
    fieldDict["data"]      = data
    fieldDict["tablename"] = tablename
    return fieldDict

def writeOFScalarList(fieldDict, route = "./"):
    # examine and create route
    if not os.path.exists(route):
        os.makedirs(route)
    filename = route + fieldDict["tablename"]
    print("writing {}".format(filename))
    with open(filename, "w") as myfile:
        myfile.write(fieldDict["tablename"] + "\n")
        myfile.write(str(fieldDict["dimension"]) + "\n")
        myfile.write("(" + "\n")
        
        for element in fieldDict["data"]:
            myfile.write(str(element) + "\n")
        
        myfile.write(");")

def readOFField(fieldname, baseRoute):
    filename  = baseRoute + fieldname

    startFlag       = False
    dimensionFlag   = False
    endFlag         = False

    dimension = 0
    data      = []

    with open(filename, "r") as myfile:
        for line in myfile.readlines():
            line = line.strip("\n")
            if (not startFlag):
                if ("internalField" in line):
                    startFlag = True
                    if (("uniform" in line) and ("nonuniform" not in line)):
                        info = line.replace("internalField","")
                        info = info.replace("uniform","")
                        info = info.replace(";","")
                        data = float(info)
                        dimension = np.nan
                        break
            else: # startFlag on
                if (not dimensionFlag):
                    if isnum(line):
                        dimension = int(line)
                        dimensionFlag = True
                else: # startFlag on, dimensionFlag on
                    if (not endFlag):
                        if (isnum(line)):
                            data.append(float(line))
                        elif (")" in line):
                            endFlag = True
                            break
                        else:
                            pass
                    
    fieldDict = {}
    fieldDict["tablename"] = fieldname
    fieldDict["dimension"] = dimension
    fieldDict["data"] = data
    return fieldDict
