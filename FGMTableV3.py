import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from copy import deepcopy
from desert import isnum
from pfunctions import getTimeSteps
from readOFFiles import readOFField
from readOFFiles import readOFScalarList
from readOFFiles import writeOFScalarList
from scipy.interpolate import interp1d
from scipy.interpolate import griddata

class FGMtable:
    def __init__(self, dict):
        self.dict = dict
        self.Zrange = dict["Zrange"]
        self.gridNumber = dict["gridNumber"]
        self.gridPower  = dict["gridPower"]
        self.route = dict["route"]
        self.timeSteps  = getTimeSteps(self.route)
        self.timeSteps.remove("0")
        self.ZList      = self.constructZList()
        self.CList      = self.constructCList()
        self.fuelList   = self.constructFuelList()
        self.ZCenterList = self.constructZCenterList()
        self.CCenterList = self.constructCCenterList()
        self.PVFields = self.constructPVFields()
        self.PVCoeffs = self.constructPVCoeffs()
        self.extraLookupFields = self.constructExtraLookupFields()
        self.readFields = self.constructReadFields()
        self.lookupFields = self.constructLookupFields()
        self.extraLookupFields = self.constructExtraLookupFields()
        self.dataSizePerFile = None
        self.fieldData = None
        self.pdFieldData = None
        self.FGMFields = None
        self.tableFieldDict = None

    def constructFuelList(self):
        return self.dict["fuelList"]

    def constructPVFields(self):
        PVFields = []
        for field in self.dict["PVFields"]:
            PVFields.append(field)
        return PVFields
    
    def constructPVCoeffs(self):
        PVCoeffs = []
        for coeff in self.dict["PVCoeffs"]:
            PVCoeffs.append(coeff)

        # size check
        if (np.size(PVCoeffs) == np.size(self.PVFields)):
            return PVCoeffs
        else:
            raise Exception("The size of PVCoeffs and PVFields are not equal! Please check the input!")

    def constructReadFields(self):
        readFields = deepcopy(self.PVFields)
        for field in self.fuelList:
            readFields.append(field)
        for PVField in self.PVFields:
            readFields.append("R_" + PVField)
        for extraField in self.extraLookupFields:
            readFields.append(extraField)
        readFields.append("thermo:psi")
        readFields.append("thermo:kappa")
        readFields.append("thermo:mu")
        readFields.append("T")
        readFields.append("Z")

        
        # for field in self.dict["lookupFields"]:
        #     if field in readFields:
        #         pass
        #     else:
        #         readFields.append(field)
        return readFields
    
    def constructExtraLookupFields(self):
        return self.dict["extraLookupFields"]
    
    def constructLookupFields(self):
        lookupFields = ["thermo:psi","thermo:kappa","thermo:mu","T","PVMax","PVMin","SourcePV"]
        for fuel in self.fuelList:
            lookupFields.append(fuel)
            
        for extraField in self.extraLookupFields:
            lookupFields.append(extraField)
        return lookupFields

    def info(self):
        print("ZRange: {}".format(self.Zrange))
        print("grid number in Z/C dimensions: {}".format(self.gridNumber))
        print("grid power  in Z/C dimensions: {}".format(self.gridPower))
        print("PV expression: ")
        PVExpressionList = []
        for i in range(len(self.PVFields)):
            PVExpressionList.append(str(self.PVCoeffs[i]) + "x" + self.PVFields[i])
        PVExpression = "+".join(PVExpressionList)
        print(PVExpression)
        print("Lookup Fields: {}".format(self.lookupFields))
        

    def constructZList(self):
        maxZ        = self.Zrange[1]
        gridNumberZ = self.gridNumber[0] 
        gridPowerZ  = self.gridPower[0]
        normalizedZList = np.linspace(0, maxZ, gridNumberZ)
        return maxZ * normalizedZList**gridPowerZ

    def constructCList(self):
        maxC = 1
        gridNumberC = self.gridNumber[1]
        gridPowerC  = self.gridPower[1]
        normalizedCList = np.linspace(0, maxC, gridNumberC)
        return maxC * normalizedCList**gridPowerC
    
    def constructZCenterList(self):
        ZCenterList = np.zeros(np.size(self.ZList)-1)
        for i in range(np.size(self.ZList)-1):
            ZCenterList[i] = (self.ZList[i] + self.ZList[i+1])/2
        return ZCenterList
    
    def constructCCenterList(self):
        CCenterList = np.zeros(np.size(self.CList)-1)
        for i in range(np.size(self.CList)-1):
            CCenterList[i] = (self.CList[i] + self.CList[i+1])/2
        return CCenterList

    def findIndex(self, dataList, value):
        index = np.argmin(np.abs(value-dataList))
        return index
            


    def readRawData(self):
        route = self.route
        timeSteps = getTimeSteps(route)
        timeSteps.remove("0")
        numOfFields = len(self.readFields)

        # try with one file to get dimensions
        tryField = self.readFields[0]
        tryTime  = timeSteps[0]
        tryRoute = route + "/" + tryTime + "/"
        tryFieldDict = readOFField(tryField, tryRoute)
        
        self.dataSizePerFile = tryFieldDict["dimension"]
        
        allFieldData = np.zeros((0,numOfFields))
        print("\n")
        for timeStep in timeSteps:
            thisTimeStepFieldData = np.zeros((self.dataSizePerFile,numOfFields))
            
            print("Reading data from time = {}".format(timeStep), end = "\r")
            for i, field in enumerate(self.readFields):
                try:
                    fieldRoute = route + "/" + timeStep + "/" 
                    thisTimeFieldDict = readOFField(field, fieldRoute)
                    thisTimeStepFieldData[:,i] = thisTimeFieldDict["data"]
                except:
                    print("Cannot read field {} at timestep {}".format(field, timeStep))
                    if (field == "Z"):
                        raise Exception("The tabulation cannot proceed without Z")
            allFieldData = np.concatenate((allFieldData, thisTimeStepFieldData), axis = 0)
            self.fieldData = allFieldData
        print("\n")
        
    def rawDataToPandas(self, releaseMemory = True):
        print("\nConverting data to pandas array")
        df = pd.DataFrame(self.fieldData, columns = self.readFields)
        
        if (releaseMemory):
            self.fieldData = None
        
        self.pdFieldData = df

    def timeToIndex(self, time):
        listTimeSteps = list(self.timeSteps)
        index = listTimeSteps.index(time)
        return index

    def selectTimeStepWithPD(self, time):
        index = self.timeToIndex(time)
        startIndexInPDArrays = index     * self.dataSizePerFile
        endIndexInPDArrays   = (index+1) * self.dataSizePerFile
        selectedRows = self.pdFieldData[startIndexInPDArrays:endIndexInPDArrays]
        return selectedRows
    
    def constructDFForOneTimeStep(self, data):
        columnnames = list(data.columns)
        columnnames.remove("Z")

        dfResult = pd.DataFrame()
        dfResult["Z"] = self.ZList
        for columnname in columnnames:
            interpFunc  = interp1d(data["Z"], data[columnname], kind = "linear", bounds_error = False, fill_value = (data[columnname].iloc[0], data[columnname].iloc[-1]))
            interpValue = interpFunc(self.ZList)
            dfResult[columnname] = interpValue
        return dfResult 

    def constructDFForAllTimeSteps(self):
        print("\nConstructing dataframe for all timesteps")
        allInterpPDArray = pd.DataFrame()
        timeSteps = list(self.timeSteps)
        for time in timeSteps:
            print("\tProcessing time = {}".format(time), end = "\r")
            pdArray = self.selectTimeStepWithPD(time)
            interpPDArray = self.constructDFForOneTimeStep(pdArray)
            allInterpPDArray = pd.concat([allInterpPDArray, interpPDArray], axis = 0)
        self.pdInterpFieldData = allInterpPDArray
        return allInterpPDArray
    
    def checkForMonotonicProperties(self):
        returndata = self.pdInterpFieldData.copy()
        for timeIndex in range(len(self.timeSteps)-1):
            timeIndexPlus = timeIndex + 1
            timeIndexPlusPlus = timeIndex + 2

            curTimeStart = timeIndex*len(self.ZList)
            curTimeStop  = timeIndexPlus*len(self.ZList)

            nextTimeStart = timeIndexPlus*len(self.ZList)
            nextTimeStop   = timeIndexPlusPlus*len(self.ZList)

            thisTimeData = returndata[curTimeStart:curTimeStop]
            nextTimeData = returndata[nextTimeStart:nextTimeStop].copy()

            if (len(thisTimeData) != len(nextTimeData)):
                raise Exception("The data sizes of two timesteps are not equal")
            else:
                # check whether PV is monotonically increasing
                for index in range(len(thisTimeData)):
                    if (thisTimeData.loc[index, "PV"] > nextTimeData.loc[index,"PV"]):
                        nextTimeData.loc[index] = thisTimeData.loc[index]
                returndata[nextTimeStart:nextTimeStop] = nextTimeData
        self.pdMonoInterpFieldData = returndata
        return returndata


    def getPVMinMaxAndScaledPV(self):
        print("\nGet PVmin, PVmax, and scaledPV")
        data = self.pdInterpFieldData
        PV = data["PV"]
        PV = np.reshape(list(PV), (-1, len(self.ZList)))
        self.PVMax = np.max(PV, axis = 0)
        self.PVMin = np.min(PV, axis = 0)

        
        scaledPV = (PV - self.PVMin)/(self.PVMax - self.PVMin + 1e-12)
        
        self.pdInterpFieldData["scaledPV"] = np.reshape(scaledPV, (-1,))
    
    def getZPVGrid(self):
        print("\nGet Z and PV grids")
        self.PVGrid = np.zeros((len(self.CList), len(self.ZList)))
        self.ZGrid  = np.zeros((len(self.CList), len(self.ZList)))
        for i in range(len(self.ZList)):
            tempCGrid = np.linspace(self.PVMin[i], self.PVMax[i], len(self.CList))
            self.PVGrid[:,i] = tempCGrid
            self.ZGrid[:,i]  = self.ZList[i]      
        
    

    def addPV(self):
        print("\nAdding PV")
        PV = np.zeros(len(self.pdFieldData))
        for i in range(len(self.PVFields)):
            PV += self.pdFieldData[self.PVFields[i]] * self.PVCoeffs[i]
        self.pdFieldData["PV"] = PV

    def addSourcePV(self):
        print("\nAdding SourcePV")
        SourcePV = np.zeros(len(self.pdFieldData))
        for i in range(len(self.PVFields)):
            R_PVFields = "R_" + self.PVFields[i]
            SourcePV += self.pdFieldData[R_PVFields] * self.PVCoeffs[i]
        self.pdFieldData["SourcePV"] = SourcePV


    def generateFGMFields(self):
        print("\nGenerating FGM tables")
        # create an empty dictionary
        emptyFieldDict = {}
        
        for field in self.lookupFields:
            if ((field != "PVMax") and (field != "PVMin")):
                print("Dealing with field {}".format(field))
                resultArray = np.zeros((len(self.CList), len(self.ZList)))
                fieldValue = np.reshape(list(self.pdInterpFieldData[field]),(-1,len(self.ZList)))
                PVValue = np.reshape(list(self.pdInterpFieldData["PV"]), (-1, len(self.ZList)))
                ZValue  = np.reshape(list(self.pdInterpFieldData["Z"]),(-1, len(self.ZList)))

                interp_linear  = griddata((ZValue.reshape(-1), PVValue.reshape(-1)), fieldValue.reshape(-1), (self.ZGrid.reshape(-1), self.PVGrid.reshape(-1)), method = 'linear')
                interp_nearest = griddata((ZValue.reshape(-1), PVValue.reshape(-1)), fieldValue.reshape(-1), (self.ZGrid.reshape(-1), self.PVGrid.reshape(-1)), method = 'nearest')

                # deal with out-of-bound values
                oob = np.isnan(interp_linear)
                interp_linear[oob] = interp_nearest[oob]

                
                emptyFieldDict[field] = interp_linear.reshape((-1, len(self.ZList)))
            elif (field == "PVMax"):
                resultArray = np.zeros((len(self.CList), len(self.ZList)))
                for index in range(len(self.ZList)):
                    resultArray[:,index] = self.PVMax[index]
                emptyFieldDict[field] = resultArray

            elif (field == "PVMin"):
                resultArray = np.zeros((len(self.CList), len(self.ZList)))
                for index in range(len(self.ZList)):
                    resultArray[:,index] = self.PVMin[index]
                emptyFieldDict[field] = resultArray
            else:
                pass            
        self.FGMFields = emptyFieldDict
        print("\n")
        return emptyFieldDict
       
        
        # add FGMFields to object data member
        self.FGMFields  = FGMFields

    def statistics(self):
        pass


    def writeTables(self,route = "./tableV3/"):
        for field in self.lookupFields:
            # prepare for the name of the field
            writename = ""
            if (field == "thermo:mu"):
                writename = "mu_table"
            elif (field == "thermo:psi"):
                writename = "psi_table"
            elif (field == "thermo:kappa"):
                writename = "kappa_table"
            elif (field == "PVMax"):
                writename = "PVmax_table"
            elif (field == "PVMin"):
                writename = "PVmin_table"
            elif (field == "HRR"):
                writename = "Qdot"
                
            else:
                writename = field + "_table"
            
            # prepare for the field data
            fieldDict = {}
            orgData = self.FGMFields[field]
            orgData = np.reshape(orgData.transpose(),(-1))
            fieldDict["tablename"] = writename
            fieldDict["dimension"] = np.size(orgData)
            fieldDict["data"] = orgData

            writeOFScalarList(fieldDict,route)


    def Allrun(self, readRoute = "./", writeRoute = "./tableV3/"):
        self.info()
        self.readRawData()
        self.rawDataToPandas()
        self.addPV()
        self.addSourcePV()
        allDf = self.constructDFForAllTimeSteps()
        self.getPVMinMaxAndScaledPV()
        self.getZPVGrid()
        self.generateFGMFields()
        self.writeTables(writeRoute)
        return self

