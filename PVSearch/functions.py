import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
from PIL import Image

def is_number(n):
    try:
        float(n)   # Type-casting the string to `float`.
                   # If string is not a valid `float`, 
                   # it'll raise `ValueError` exception
    except ValueError:
        return False
    return True

def isnum(n):
    return is_number(n)



def getTimeSteps(path):
    tempTimeList = os.listdir(path)
    returnTimeList = []
    floatTimeList = []

    # clean time list, emitting hidden files and other files
    for time in tempTimeList:
        if (is_number(time)):
            returnTimeList.append(time)
    floatTimeList = [float(i) for i in returnTimeList]
    # sort and return
    floatTimeList, order = sortAndOrder(floatTimeList)
    returnTimeList = [returnTimeList[i] for i in order]
    return returnTimeList

def sortAndOrder(array):
    array = np.array(array)
    index = np.argsort(array)
    array = [array[i] for i in index]
    return list(array), list(index)

def getNearestTime(time, timeSteps):
    time = float(time)
    floatTimeSteps = np.array([float(i) for i in timeSteps])
    error = np.abs(time-floatTimeSteps)
    index = np.argmin(error)
    return timeSteps[index]

