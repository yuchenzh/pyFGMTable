import numpy as np
import matplotlib.pyplot as plt
from pfunctions import getTimeSteps

class TimeSteps:
    # ----- Data member ----- #
    #- 1) caseRoute
    #- 2) lowerBound
    #- 3) upperBound
    #- 4) stepEvery
    #- 5) timeStepList
    #- 6) usedTimeStepList

    # ----- Function member ----- #
    # --- construcctor --- #
    def __init__(self, caseRoute, lowerBound = None, upperBound = None, stepEvery = 1):
        self.caseRoute = caseRoute
        self.lowerBound = lowerBound
        self.upperBound = upperBound
        self.stepEvery = stepEvery
        self.timeStepList = getTimeSteps(caseRoute)

        if (lowerBound != None and upperBound != None):
            self.usedTimeStepList = self.preserveTimeStep(self.timeStepList)
        
        if (stepEvery != 1):
            self.usedTimeStepList = self.keepEvery(self.usedTimeStepList)

        
        


    # --- overloaded operators --- #
    def __call__(self):
        return self.usedTimeStepList


    # --- other functions --- #
    def preserveTimeStep(self,timeStepList):
        usedTimeStepList = []
        for i in timeStepList:
            if (float(i) > self.lowerBound - 1e-12 and float(i) < self.upperBound+1e-12):
                usedTimeStepList.append(i)
        return usedTimeStepList
    
    def keepEvery(self, timeStepList):
        usedTimeStepList = timeStepList[::self.stepEvery]
        return usedTimeStepList
