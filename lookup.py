import numpy as np
import matplotlib.pyplot as plt
from readOFFiles import readOFScalarList

# --- relevant functions --- #
def findBetween(value, array):
    # the array should be monotonically increasing
    if (value <= array[0]):
        indexPair = (0,1)
        coeffPair = (1,0)
    elif (value >= array[-1]):
        indexPair = (len(array)-2, len(array)-1)
        coeffPair = (0,1)
    else:
        for i in range(len(array)):
            if (value > array[i]):
                indexPair = (i, i+1)

                coeffLeft = (array[i+1] - value)/(array[i+1] - array[i])
                coeffPair = (coeffLeft, 1-coeffLeft)
    return indexPair, coeffPair

def lookupInList(fieldList, indexPair, coeffPair):
    return fieldList[indexPair[0]]*coeffPair[0] + fieldList[indexPair[1]]*coeffPair[1]


class lookup:
    # ----- Data member ----- #
    #- 1) tableRoute
    #- 2) controlVariableNames
    #- 3) controlVariableFields
    #- 4) lookupVariableNames
    #- 5) lookupVariableFields

    # ----- Function member ----- #
    # --- constructor --- #
    def __init__(self, tableRoute, controlVariableNames,lookupVariableNames):
        self.tableRoute = tableRoute
        self.controlVariableNames = controlVariableNames
        self.lookupVariableNames = lookupVariableNames
        self.controlVariableNames.append("PVmin")
        self.controlVariableNames.append("PVmax")

        self.controlVariableFields = self.loadControlVariableFields()
        self.lookupVariableFields = self.loadLookupVariableFields()

    # --- overloaded operators

    # --- other functions --- #
    def loadField(self, fieldname):
        fieldDict = readOFScalarList(fieldname, self.tableRoute)
        field = np.array(fieldDict["data"])
        return field

    def loadControlVariableFields(self):
        CVFieldDict = {}
        for name in self.controlVariableNames:
            tablename = name + "_table"
            field = self.loadField(tablename)
           
            if ((name == "PVmin") or (name == "PVmax")):
                field = np.reshape(field, (len(CVFieldDict["Z"]), len(CVFieldDict["scaledPV"]))).transpose()
                field = field[0,:]
            CVFieldDict[name] = field
        return CVFieldDict
            
    
    def loadLookupVariableFields(self):
        LUFieldDict = {}
        for name in self.lookupVariableNames:
            tablename = name + "_table"
            field = self.loadField(tablename)
            field = np.reshape(field, (len(self.controlVariableFields["Z"]), len(self.controlVariableFields["scaledPV"]))).transpose()
            LUFieldDict[name] = field
        return LUFieldDict

    def __call__(self, Z, C, fieldname):
        indexPair, coeffPair = findBetween(Z, self.controlVariableFields["Z"])
        PVmin = lookupInList(self.controlVariableFields["PVmin"], indexPair, coeffPair)
        PVmax = lookupInList(self.controlVariableFields["PVmax"], indexPair, coeffPair)
        scaledPV = (C-PVmin)/(PVmax-PVmin + 1e-8)

        ZindexPair, ZcoeffPair   = findBetween(Z       , self.controlVariableFields["Z"])
        PVindexPair, PVcoeffPair = findBetween(scaledPV, self.controlVariableFields["scaledPV"])
        
        result = \
            ZcoeffPair[0]*PVcoeffPair[0]*self.lookupVariableFields["T"][PVindexPair[0]][ZindexPair[0]] + \
            ZcoeffPair[0]*PVcoeffPair[1]*self.lookupVariableFields["T"][PVindexPair[0]][ZindexPair[1]] + \
            ZcoeffPair[1]*PVcoeffPair[0]*self.lookupVariableFields["T"][PVindexPair[1]][ZindexPair[0]] + \
            ZcoeffPair[1]*PVcoeffPair[1]*self.lookupVariableFields["T"][PVindexPair[1]][ZindexPair[1]]
                    
        return result
