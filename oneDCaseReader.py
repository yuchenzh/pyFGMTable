import numpy as np
import matplotlib.pyplot as plt
from pfunctions import *
from readOFFiles import readOFField

class oneDCaseReader:
    # ----- Data member ----- #
    #- 1) caseRoute
    #- 2) grid

    # ----- Function member ----- #
    # --- constructor --- #
    def __init__(self, caseRoute):
        self.caseRoute = caseRoute

    # --- overloaded operators --- #
    def __call__(self, timeStep, fieldname):
        return self.readData(timeStep, fieldname)
    
    # --- other functions --- #
    def readData(self, timeStep, fieldname):
        timeSteps = getTimeSteps(self.caseRoute)
        timeStep = getNearestTime(timeStep, timeSteps)

        fieldDict = readOFField(fieldname, self.caseRoute + timeStep + "/")
        field = fieldDict["data"]
        return field