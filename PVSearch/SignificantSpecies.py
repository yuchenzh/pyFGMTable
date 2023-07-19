from functions import getTimeSteps, getNearestTime
from TimeSteps import TimeSteps
from readOFFiles import readOFField, readOFScalarList, writeOFScalarList
import numpy as np
import pandas as pd

class significantSpecies:

    # ===== Data member ===== #
    #- 1) sDict : species dictionary\
    #- 2) caseRoute
    #- 3) startTime
    #- 4) endTime
    #- 5) stepEvery
    #- 6) timeStepList
    #- 7) speciesList
    #- 8) SumRRi: sum of absolute reaction for species i over time (pandas dataframe)
    #- 9) SumRRiOverTimeAndSpace: sum of absolute reaction for species i over time and space,
    # ---  and sort the results(pandas dataframe)
    #- 10) SumRRiOverSpecies: sum of absolute reaction for all species over time (pandas dataframe)

 
    # ===== Constructor ===== #
    def __init__(self, sDict):   
        self.dict = sDict
        self.caseRoute = sDict["caseRoute"]
        self.startTime = sDict["startTime"]
        self.endTime = sDict["endTime"]
        self.stepEvery = sDict["stepEvery"]
        self.timeStepList = TimeSteps(self.caseRoute, self.startTime, self.endTime, self.stepEvery)()
        #exclude 0 in self.timeStepList
        if (self.timeStepList[0] == "0"):
            self.timeStepList = self.timeStepList[1:]
        self.speciesList = sDict["speciesList"]   
        self.SumRRi = None   
        self.SumRRiOverTimeAndSpace = None
        self.SumRRiOverSpecies = None
        
        
    # ===== Function member ===== #
    
    def readFieldAtTime(self, field, time):
        nearestTime = getNearestTime(time, self.timeStepList)
        fieldDict = readOFField(field, self.caseRoute + "/" + nearestTime + "/")
        field = fieldDict["data"]
        return field
        
        
    def generateSumRRiForEachSpeciesOverTime(self,fieldname, startTime, endTime):

        usedTimeStepList = TimeSteps(self.caseRoute, startTime, \
            endTime, self.stepEvery)()
        #exclude 0 in usedTimeStepList
        if (usedTimeStepList[0] == "0"):
            usedTimeStepList = usedTimeStepList[1:]
        
        # try to read a field to get its size
        tryField = self.readFieldAtTime(fieldname, usedTimeStepList[0])
        
        # initialize the sum
        SumRRi = np.zeros_like(tryField)
        
        # loop over time
        for time in usedTimeStepList:
            fieldvalue = self.readFieldAtTime("R_" + fieldname, time)
            SumRRi += np.abs(fieldvalue)
        return SumRRi
    
    def generateSumRRi(self, startTime = None, endTime = None):
        if (startTime == None):
            startTime = self.startTime
        if (endTime == None):
            endTime = self.endTime
        
        # generate a dictionary for the sum of absolute reaction rate for each species
        SumRRiDict = {}
        for species in self.speciesList:
            SumRRiDict[species] = \
                self.generateSumRRiForEachSpeciesOverTime(species,startTime, endTime)
        
        # generate the SumRRi dataframe
        SumRRi = pd.DataFrame(SumRRiDict)
        self.SumRRi = SumRRi
        
        # generate most significant species 
        self.SumRRiOverTimeAndSpace = self.SumRRi.sum(axis = 1).sort_values(ascending = False, inplace = True)
        

    def generateSumRRiOverSpecies(self):
        # try to read a field to get its size
        tryField = self.readFieldAtTime(self.speciesList[1],self.timeStepList[0])
        resultDict = {}
        
        # for each time step
        for timeStep in self.timeStepList:
            result = np.zeros_like(tryField) # initialize
            for species in self.speciesList:
                # read species field
                fieldvalue = self.readFieldAtTime("R_"+species, timeStep)
                result += np.abs(fieldvalue)
            resultDict[timeStep] = result
        
        # convert the resultDict to pandas dataframe
        result = pd.DataFrame(resultDict)
        self.SumRRiOverSpecies = result
        
    
    def normalizedRR(self, RR):
        return RR/np.max(np.abs(RR))
    
    def optimizedPVDirection(self, startTime = None, endTime = None, threshold = 1e-1):
        # if the startTime and endTime are not specified, use the default values
        if (startTime == None):
            startTime = self.startTime
        if (endTime == None):
            endTime = self.endTime
        
        timeSteps = TimeSteps(self.caseRoute, startTime, endTime, self.stepEvery)()
        if ('0' in timeSteps):
            timeSteps.remove('0')
            
        # try to read a field to determine the size of the field
        tryField = self.readFieldAtTime(self.speciesList[0], timeSteps[0])
        fieldSize = np.size(tryField)
        
        # iterate over each timestep -> each grid, extract useful significant reactions
        # initialize the RR matrix in a timeStep, each column is the RR vector for a point
        optimizedRRMatrix = np.array([])
        for timeStep in timeSteps:
            tempRRMatrix = np.zeros((len(self.speciesList), fieldSize))
            for i, species in enumerate(self.speciesList):
                # read species field
                fieldvalue = self.readFieldAtTime("R_"+species, timeStep)
                tempRRMatrix[i,:] = fieldvalue
        
            # determine the trival columns, record their index and delete them in the future
            invalidColumnIndex = []
            for column in range(fieldSize):
                if (np.sum(np.abs(tempRRMatrix[:,column])) < threshold):
                    invalidColumnIndex.append(column)
            tempRRMatrix = np.delete(tempRRMatrix, invalidColumnIndex, axis = 1)
    
            # concatenate the RRMatrix
            if (np.size(optimizedRRMatrix) == 0) and (np.size(tempRRMatrix) > 0):
                optimizedRRMatrix = tempRRMatrix
            else:
                optimizedRRMatrix = np.concatenate((optimizedRRMatrix, tempRRMatrix), axis = 1)
            
            
        # normalized the optimizedRRMatrix
        normalizedOptimizedRRMatrix = np.zeros_like(optimizedRRMatrix)
        for i in range(np.shape(optimizedRRMatrix)[1]):
            normalizedOptimizedRRMatrix[:,i] = self.normalizedRR(optimizedRRMatrix[:,i])
    
        # calculate the mean direction        
        meanDirection = np.mean(normalizedOptimizedRRMatrix, axis = 1)
        
        return meanDirection
                
        
    # ===== Overloaded operators ===== #