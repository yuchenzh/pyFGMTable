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
from tableProperties import FGMtableProperties
import pickle
import os

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
        self.PVConstant = dict["PVConstant"]
        self.extraLookupFields = self.constructExtraLookupFields()
        self.readFields = self.constructReadFields()
        self.lookupFields = self.constructLookupFields()
        self.extraLookupFields = self.constructExtraLookupFields()
        self.dataSizePerFile = None
        self.fieldData = None
        self.pdFieldData = None
        self.FGMFields = None
        self.tableFieldDict = None
        self.PV0 = None
        self.Z0  = None

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
        PVExpression +=  "+ " + str(self.PVConstant)
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
            
    def getPV0(self):
        PV0 = np.array(self.pdFieldData[0:self.dataSizePerFile]["PV"])
        Z0  = np.array(self.pdFieldData[0:self.dataSizePerFile]["Z"])
        self.PV0 = PV0
        self.Z0  = Z0

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
        print("\nConstructing data for all timesteps")
        allInterpPDArray = pd.DataFrame()
        timeSteps = list(self.timeSteps)
        for time in timeSteps:
            print("Constructing data for time = {}".format(time), end = "\r")
            pdArray = self.selectTimeStepWithPD(time)
            interpPDArray = self.constructDFForOneTimeStep(pdArray)
            allInterpPDArray = pd.concat([allInterpPDArray, interpPDArray], axis = 0)
        self.pdInterpFieldData = allInterpPDArray
        self.pdInterpFieldData.reset_index(drop = True,inplace = True)
        print("\n")
        return allInterpPDArray
    
    def checkForMonotonicProperties(self):
        print("\nChecking monotonic properties")
        returndata = self.pdInterpFieldData.copy()
        for timeIndex in range(len(self.timeSteps)-1):
            print("\t Repairing time = {}".format(self.timeSteps[timeIndex]), end = "\r")
            timeIndexPlus = timeIndex + 1
            timeIndexPlusPlus = timeIndex + 2

            curTimeStart = timeIndex*len(self.ZList)
            curTimeStop  = timeIndexPlus*len(self.ZList)

            nextTimeStart = timeIndexPlus*len(self.ZList)
            nextTimeStop   = timeIndexPlusPlus*len(self.ZList)

            thisTimeData = returndata[curTimeStart:curTimeStop].copy()
            nextTimeData = returndata[nextTimeStart:nextTimeStop].copy()
            thisTimeData = thisTimeData.reset_index(drop = True)
            nextTimeData = nextTimeData.reset_index(drop = True)
            #nextTimeData.reset_index(drop = True, inplace = True)
            

            if (len(thisTimeData) != len(nextTimeData)):
                raise Exception("The data sizes of two timesteps are not equal")
            else:
                # check whether PV is monotonically increasing
                for index in range(len(thisTimeData)):
                    if (thisTimeData.loc[index,"PV"] > nextTimeData.loc[index,"PV"]):
                        nextTimeData.loc[index] = thisTimeData.loc[index]
                returndata[nextTimeStart:nextTimeStop] = nextTimeData
        returndata.reset_index(drop = True, inplace = True)
        self.pdMonoInterpFieldData = returndata
        print("\n")
        return returndata


    def getPVMinMaxAndScaledPV(self):
        print("Calculating PVMinMax and scaled PV")
        data = self.pdMonoInterpFieldData
        PV = data["PV"]
        PV = np.reshape(list(PV), (-1, len(self.ZList)))
        self.PVMax = np.max(PV, axis = 0)
        self.PVMin = np.min(PV, axis = 0)

        
        scaledPV = (PV - self.PVMin)/(self.PVMax - self.PVMin + 1e-12)
        
        self.pdMonoInterpFieldData["scaledPV"] = np.reshape(scaledPV, (-1,))
        print("\n")

    def getScaledPVForPostProcessing(self):
        print("\nGet PVmin, PVmax, and scaledPV for post-processing")
        data = self.pdInterpFieldData
        PV = data["PV"]
        PV = np.reshape(list(PV), (-1, len(self.ZList)))
        self.PVMax = np.max(PV, axis = 0)
        self.PVMin = np.min(PV, axis = 0)

        
        scaledPV = (PV - self.PVMin)/(self.PVMax - self.PVMin + 1e-12)
        self.pdInterpFieldData["scaledPV"] = np.reshape(scaledPV, (-1,))
        
        
    

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

    def addZIndexForPostProcessing(self):
        print("\nAdding ZIndex for post-processing")
        if (not self.pdInterpFieldData.empty):
            self.pdInterpFieldData["ZIndex"] = 0
            
            totalLine = len(self.pdInterpFieldData)
            for line in range(len(self.pdInterpFieldData)):

                
                #print("\tProcessing data entry {}/{}".format(line, totalLine), end = "\r")
                self.pdInterpFieldData.loc[line,"ZIndex"] = self.findIndex(self.ZCenterList, self.pdInterpFieldData.iloc[line]["Z"])
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

    def addCIndexForPostProcessing(self):
        print("\nAdding CIndex for post-processing")
        if (not self.pdInterpFieldData.empty):
            self.pdInterpFieldData["CIndex"] = 0
            totalLine = len(self.pdInterpFieldData)
            for line in range(len(self.pdInterpFieldData)):
                #print("\tProcessing data entry {}/{}".format(line, totalLine), end = "\r")
                self.pdInterpFieldData.loc[line,"CIndex"] = self.findIndex(self.CCenterList, self.pdInterpFieldData.iloc[line]["scaledPV"])
        else:
            raise Exception("The data should be loaded and converteed to pandas array before adding ZGrid")
        print("\n")

    def addPV(self):
        print("\nAdding PV")

        ## calculate PV
        PV = np.zeros(len(self.pdFieldData))
        for i in range(len(self.PVFields)):
            PV += self.pdFieldData[self.PVFields[i]] * self.PVCoeffs[i]
        PV += self.PVConstant
        self.pdFieldData["PV"] = PV

        ## repair PV
        self.getPV0()
        fPV0 = interp1d(self.Z0, self.PV0, kind = 'linear', bounds_error = False, fill_value = (self.PV0[0], self.PV0[-1]))
        localPV0 = fPV0(self.pdFieldData["Z"])
        PV = PV - localPV0
        # for i in range(len(self.pdFieldData)):
        #     localPV0 = fPV0(self.pdFieldData["Z"][i])
        #     PV[i] = PV[i] - localPV0
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
                fieldValue = np.reshape(list(self.pdMonoInterpFieldData[field]),(-1,len(self.ZList)))
                scaledPVValue = np.reshape(list(self.pdMonoInterpFieldData["scaledPV"]), (-1, len(self.ZList)))
                
                noPVIndices = np.where(np.abs(self.PVMax - self.PVMin) < 1e-8)
                noPVIndices = noPVIndices[0].tolist()
                for noPVIndex in noPVIndices:
                    resultArray[:,noPVIndices] = np.mean(fieldValue[:,noPVIndex])
                
                for index in range(len(self.ZList)):
                    if (index not in noPVIndices):
                        x = scaledPVValue[:,index]
                        y = fieldValue[:,index]
                        interpFunc = interp1d(x, y, kind = 'linear',  bounds_error=False, fill_value=(y[0],y[-1]))
                        resultArray[:,index] = interpFunc(self.CList)
                
                emptyFieldDict[field] = resultArray
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
       
        

    def statistics(self,saveRoute = "./tableV2/"):
        # Add Z/ C indexes
        self.addZIndexForPostProcessing()
        self.getScaledPVForPostProcessing()
        self.addCIndexForPostProcessing()

        # add resultCabins storing all interpolated data
        import copy
        resultCabinDict = {}
        for lookupField in self.lookupFields:
            resultCabinDict[lookupField] = []

        resultCabins = [[] for ZCenterEle in self.ZCenterList]
        for i in range(len(resultCabins)):
            resultCabins[i] = [copy.deepcopy(resultCabinDict)  for CCenterEle in self.CCenterList]

        for ele in range(len(self.pdInterpFieldData)):
            CIndex = self.pdInterpFieldData.loc[ele,"CIndex"]
            ZIndex = self.pdInterpFieldData.loc[ele,"ZIndex"]
            for lookupField in self.lookupFields:
                if ((lookupField != "PVMax") and (lookupField != "PVMin")):
                    resultCabins[ZIndex][CIndex][lookupField].append(self.pdInterpFieldData.iloc[ele][lookupField])

        self.resultCabins = resultCabins

        statisticsCabinDict = {}
        for lookupField in self.lookupFields:
            statisticsCabinDict[lookupField] = {}
            statisticsCabinDict[lookupField]["mean"] = np.nan
            statisticsCabinDict[lookupField]["std"]  = np.nan
            
        statisticsCabins = [[] for ZCenterEle in self.ZCenterList]
        for i in range(len(statisticsCabins)):
            statisticsCabins[i] = [copy.deepcopy(statisticsCabinDict) for CCenterEle in self.CCenterList]

        for ZI in range(len(self.ZCenterList)):
            for CI in range(len(self.CCenterList)):
                for lookupField in self.lookupFields:
                    statisticsCabins[ZI][CI][lookupField]["mean"] = np.nanmean(resultCabins[ZI][CI][lookupField])
                    if (len(resultCabins[ZI][CI][lookupField]) < 2):
                        statisticsCabins[ZI][CI][lookupField]["std"] = np.nan
                    else:
                        statisticsCabins[ZI][CI][lookupField]["std"] = np.std(resultCabins[ZI][CI][lookupField])

        self.statisticsCabins = statisticsCabins

        ## plot mean, std, std/mean
        # create the directory for storing the statistics results
        targetRoute = saveRoute + "/" + "statistics" + "/"
        if (not os.path.isdir(targetRoute)):
            os.mkdir(targetRoute)
        ZZ,CC = np.meshgrid(self.ZCenterList, self.CCenterList)
        for fieldname in self.lookupFields:
            if ((fieldname != "PVMin") and (fieldname != "PVMax")):
                print("plotting statistics for field {}".format(fieldname))
                meanField = self.getMeanFieldForStatistics(fieldname)
                stdField  = self.getStdFieldForStatistics(fieldname)
                ratioField = np.abs(stdField/meanField)

                # plot
                plt.figure(figsize = (5,9))
                plt.subplot(311)
                plt.pcolor(ZZ,CC,meanField, cmap = "hot")
                plt.xlabel("Z")
                plt.ylabel("Value")
                plt.colorbar()
                plt.title(fieldname + "mean")

                plt.subplot(312)
                plt.pcolor(ZZ,CC,stdField, cmap = "hot")
                plt.xlabel("Z")
                plt.ylabel("Value")
                plt.colorbar()
                plt.title(fieldname + "std")

                plt.subplot(313)
                plt.pcolor(ZZ,CC,ratioField, cmap = "hot")
                plt.xlabel("Z")
                plt.ylabel("Value")
                plt.clim(0,1)
                plt.colorbar()
                plt.title(fieldname + "std/" + fieldname + "mean")

                plt.tight_layout()
                plt.savefig(targetRoute + fieldname + ".png")
                plt.clf()
                plt.close()
                        
        
    def getMeanFieldForStatistics(self, fieldname):
        fieldmean = np.zeros((len(self.CCenterList), len(self.ZCenterList)))

        for ZI in range(len(self.ZCenterList)):
            for CI in range(len(self.CCenterList)):
                fieldmean[CI][ZI] = self.statisticsCabins[ZI][CI][fieldname]["mean"]
        return fieldmean
                

    def getStdFieldForStatistics(self, fieldname):
        fieldstd  = np.zeros((len(self.CCenterList), len(self.ZCenterList)))

        for ZI in range(len(self.ZCenterList)):
            for CI in range(len(self.CCenterList)):
                fieldstd[CI][ZI]  = self.statisticsCabins[ZI][CI][fieldname]["std"]
        return fieldstd


    def writeTables(self,route = "./tableFromOF/"):
        # write lookupFields
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
        
        # write Z and scaledPV Lists
        ## write Z
        fieldDict = {}
        orgData = self.ZList
        fieldDict["tablename"] = "Z_table"
        fieldDict["dimension"] = np.size(orgData)
        fieldDict["data"] = orgData
        
        writeOFScalarList(fieldDict, route)

        ## write scaledPV
        fieldDict = {}
        orgData = self.CList
        fieldDict["tablename"] = "scaledPV_table"
        fieldDict["dimension"] = np.size(orgData)
        fieldDict["data"] = orgData

        writeOFScalarList(fieldDict, route)
    
    def writeObj(self, writeRoute):
        savepath = writeRoute + "obj.pkl"
        with open(savepath, "wb") as file:
            pickle.dump(self,file)


    
    def Allrun(self,readRoute = "./", writeRoute = "./tableV2/"):
        self.info()
        self.readRawData()
        self.rawDataToPandas()
        self.addPV()
        self.addSourcePV()
        allDf = self.constructDFForAllTimeSteps()
        allDfRepaired = self.checkForMonotonicProperties()
        self.getPVMinMaxAndScaledPV()
        self.generateFGMFields()
        self.writeTables(writeRoute)

        # create property properties
        properties = FGMtableProperties(writeRoute, self.ZList, self.CList, self.lookupFields)
        properties()

        # write
        self.writeObj(writeRoute)

        return self  




