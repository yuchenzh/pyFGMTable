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
            


    def readRawData(self, route):
        timeSteps = getTimeSteps(route)
        timeSteps.remove("0")
        numOfFields = len(self.readFields)

        # try with one file to get dimensions
        tryField = self.readFields[0]
        tryTime  = timeSteps[0]
        tryRoute = route + "/" + tryTime + "/"
        tryFieldDict = readOFField(tryField, tryRoute)
        
        dataSizePerFile = tryFieldDict["dimension"]
        
        allFieldData = np.zeros((0,numOfFields))
        print("\n")
        for timeStep in timeSteps:
            thisTimeStepFieldData = np.zeros((dataSizePerFile,numOfFields))
            
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

    def addZIndex(self):
        print("\nAdding ZIndex")
        if (not self.pdFieldData.empty):
            self.pdFieldData["ZIndex"] = 0
            
            totalLine = len(self.pdFieldData)
            for line in range(len(self.pdFieldData)):
                print("\tProcessing data entry {}/{}".format(line, totalLine), end = "\r")
                self.pdFieldData.loc[line,"ZIndex"] = self.findIndex(self.ZCenterList, self.pdFieldData.loc[line]["Z"])
            print("\n")
        else:
            raise Exception("The data should be loaded and converteed to pandas array before adding ZGrid")


    def addCIndex(self):
        print("\nAdding CIndex")
        if (not self.pdFieldData.empty):
            self.pdFieldData["CIndex"] = 0
            totalLine = len(self.pdFieldData)
            for line in range(len(self.pdFieldData)):
                print("\tProcessing data entry {}/{}".format(line, totalLine), end = "\r")
                self.pdFieldData.loc[line,"CIndex"] = self.findIndex(self.CCenterList, self.pdFieldData.loc[line]["scaledPV"])
        else:
            raise Exception("The data should be loaded and converteed to pandas array before adding ZGrid")
        print("\n")


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

    def addPVMinMax(self):
        print("\nAdding PV Min/max")
        PVCabin = [[] for i in range(np.size(self.ZCenterList))]
        
        totalLine = len(self.pdFieldData)
        for i in range(len(self.pdFieldData)):
            print("\tProcessing data entry {}/{}".format(i, totalLine), end = "\r")
            cabinIndex = self.pdFieldData.loc[i,"ZIndex"]
            PVCabin[cabinIndex].append(self.pdFieldData.loc[i]["PV"])
        print("\n")
        
        self.PVCabin = PVCabin
        # get PVMin/Max
        PVMin = np.zeros(len(self.ZCenterList))
        PVMax = np.zeros(len(self.ZCenterList))
        numOfEmptyCabin = 0
        emptyCabinList = []
        for i in range(len(self.ZCenterList)):
            if (len(PVCabin[i]) == 0):
                emptyCabinList.append(i)
                numOfEmptyCabin +=1
                PVMin[i] = None
                PVMax[i] = None
            else:
                PVMin[i] = np.min(PVCabin[i])
                PVMax[i] = np.max(PVCabin[i])
        
        print("Empty Cabin List")
        for emptyCabin in emptyCabinList:
            print("\t Empty cabin list {} -> Z = {}".format(emptyCabin, self.ZCenterList[emptyCabin]))
        


        # Some Z might not have PV data, repair them by interpolation
        validPVMax = []
        validZList = []
        inValidPVMax = []
        inValidZList = []
        inValidZListIndexs = []

        for i, element in enumerate(PVMax):
            if (np.isnan(element)):
                inValidPVMax.append(element)
                inValidZList.append(self.ZCenterList[i])
                inValidZListIndexs.append(i)
            
            else:
                validPVMax.append(element)
                validZList.append(self.ZCenterList[i])
        
        f = interp1d(validZList, validPVMax, kind = 'linear', bounds_error=False, fill_value=(validPVMax[0],validPVMax[-1]))
        newInValidPVMax = f(inValidZList)

        for i, index in enumerate(inValidZListIndexs):
            PVMax[index] = newInValidPVMax[i]


        # temp code, set PVMin to 0
        for i in range(len(PVMin)):
            PVMin[i] = 0

        self.PVMin = PVMin
        self.PVMax = PVMax
        return numOfEmptyCabin
        
    def addScaledPVAndPVMinMax(self):
        print("\nCalculating ScaledPV")
        self.pdFieldData["scaledPV"] = 0.
        self.pdFieldData["PVMax"] = 0.
        self.pdFieldData["PVMin"] = 0.
        
        totalLine = len(self.pdFieldData)
        for ele in range(len(self.pdFieldData)):
            print("\tProcessing data entry {}/{}".format(ele, totalLine), end = "\r")
            ZIndex = self.pdFieldData.loc[ele,"ZIndex"]
            tempPVMax = self.PVMax[ZIndex]
            tempPVMin = self.PVMin[ZIndex]
            scaledPV = (self.pdFieldData.loc[ele,"PV"]-tempPVMin)/(tempPVMax - tempPVMin + 1e-8)
            self.pdFieldData.loc[ele, "scaledPV"] = scaledPV
            self.pdFieldData.loc[ele, "PVMax"] = tempPVMax
            self.pdFieldData.loc[ele, "PVMin"] = tempPVMin
        print("\n")

    def generateFGMFields(self):
        print("\nGenerating FGM tables in the cell centers")
        # create an empty dictionary
        emptyFieldDict = {}
        for field in self.lookupFields:
            emptyFieldDict[field] = []
        
        # create fields for Z-C grids, each grid has a result dictionary.
        FGMFields = [[] for ele in self.ZCenterList]
        for Z in range(len(FGMFields)):
            FGMFields[Z] = [deepcopy(emptyFieldDict) for ele in self.CCenterList]
        
        # add fields to Z-C grids, test with temperatrue
        totalLine = len(self.pdFieldData)
        for ele in range(len(self.pdFieldData)):
            print("\tProcessing data entry {}/{}".format(ele, totalLine), end = "\r")
            ZIndex = self.pdFieldData.loc[ele,"ZIndex"]
            CIndex = self.pdFieldData.loc[ele,"CIndex"]
            for field in self.lookupFields:
                FGMFields[ZIndex][CIndex][field].append(self.pdFieldData.loc[ele,field])
        print("\n")
        
        # add FGMFields to object data member
        self.FGMFields  = FGMFields

    def statistics(self):
        pass

    def interpolateToFields(self):
        print("\nInterpolating from cell centers to cell nodes")
        
        # generate Z and C lists
        ZList4Table = []
        CList4Table = []
        for Z in range(len(self.ZCenterList)):
            for C in range(len(self.CCenterList)):
                if (np.size(self.FGMFields[Z][C]["T"]) > 0):
                    ZList4Table.append(self.ZCenterList[Z])
                    CList4Table.append(self.CCenterList[C])
        

        # generate value fields
        tableFieldDict = {}
        for field in self.lookupFields:
            print("\tInterpolating field {}".format(field))
            VList = []
            for Z in range(len(self.ZCenterList)):
                for C in range(len(self.CCenterList)):
                    if (np.size(self.FGMFields[Z][C][field]) > 0):
                        VList.append(np.mean(self.FGMFields[Z][C][field]))
            
            # interpolate the field value to cell nodes, out of domain data are set with the nearest data
            ZZ,CC = np.meshgrid(self.ZList,self.CList)
            interp_data_linear  = griddata((ZList4Table,CList4Table), VList, (ZZ,CC), method = 'linear')
            interp_data_nearest = griddata((ZList4Table, CList4Table), VList, (ZZ,CC), method = 'nearest')
            interp_data = np.nan_to_num(interp_data_linear, nan=interp_data_nearest)

            tableFieldDict[field] = interp_data
        print("\n")
        
        self.tableFieldDict = tableFieldDict

    def writeTables(self,route = "./tableV1/"):
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
            orgData = self.tableFieldDict[field]
            orgData = np.reshape(orgData.transpose(),(-1))
            fieldDict["tablename"] = writename
            fieldDict["dimension"] = np.size(orgData)
            fieldDict["data"] = orgData

            writeOFScalarList(fieldDict,route)

    def Allrun(self, dataSource, writeTo = "./tableV1"):
        self.info()
        self.readRawData(dataSource)
        self.rawDataToPandas()
        self.addZIndex()
        self.addPV()
        self.addSourcePV()
        numOfEmptyCabin = self.addPVMinMax()
        self.addScaledPVAndPVMinMax()

        self.addCIndex()
        self.generateFGMFields()
        self.interpolateToFields()
        self.writeTables(writeTo)

        return self
        



