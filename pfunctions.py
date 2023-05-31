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

def getPngTimeSteps(path):
    timeListWithPNG = os.listdir(path)
    tempTimeList = [time.replace(".png","") for time in timeListWithPNG]
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

def getFloatTimeSteps(path):
    timeList = getTimeSteps(path)
    floatTimeList = [float(i) for i in timeList]
    return floatTimeList

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

def getTimeFieldPath(time,fieldname):
    return "./postProcessing/foam2Columns" + '/' + str(time) + '/' +"Eulerian_" + fieldname

def createFields(time, fieldname):
    path_to_file = "./postProcessing/foam2Columns/" + str(time) + "/Eulerian_" + fieldname
    if os.path.isfile(path_to_file):
        pass
    else:
        os.system("foam2Columns -fields '(" + fieldname + ")'" + " -time " + str(time))
    
    data = np.loadtxt(path_to_file, skiprows=1)
    x = data[:,0]
    y = data[:,1]
    z = data[:,2]
    field = data[:,3]

    return x,y,z,field

def plotFieldAtInitialTime(fieldname, isoFileNames,  gridOption, lineX, lineY, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath = "default", figsize = None, logZAxis = False):
    if ("log" in  fieldname):
        path = "0/" + fieldname.replace("log","")
    else:
        path = "0/" + fieldname

    settings = [isoFileNames, gridOption, lineX, lineY, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath, figsize, logZAxis]
    if os.path.isfile(path):
        plotFieldAtTime(0, fieldname, *settings)
    else:
        x,y,z,field = createFields("0", "p")
        field = field*0
        if (savepath == "default"):
            savepath = "./postProcessing/foam2Columns/0/" + fieldname + ".png"
        isoXs, isoYs = createPhiChiContours("0", isoFileNames)
        settings = [isoFileNames, gridOption, lineX, lineY, isoXs, isoYs, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, figsize, logZAxis]
        plotPureField(x, y, field, "0", savepath ,*settings)

        

def plotFieldAtAllTimes(fieldname, isoFileNames, gridOption, lineX, lineY,xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath = "default", figsize = None, logZAxis = False):
    timeSteps = getTimeSteps(".")
    settings = [isoFileNames, gridOption, lineX, lineY, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath, figsize, logZAxis]

    for time in timeSteps:
        if (time!="0"):
            print("Dealing with time = {}".format(time))
            plotFieldAtTime(float(time), fieldname,*settings)
        if (time=="0"):
            print("Dealing with time = 0")
            plotFieldAtInitialTime(fieldname, *settings)

def plotFieldAtSelectedTimes(fieldname, startTime, endTime, isoFileNames, gridOption, lineX, lineY, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath = "default", figsize = None, logZAxis = False):
    timeSteps = getTimeSteps(".")
    settings = [isoFileNames, gridOption, lineX, lineY, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savepath, figsize, logZAxis]

    for time in timeSteps:
        if ((float(time) > startTime) and (float(time) < endTime)):
            if (time!="0"):
                print("Dealing with time = {}".format(time))
                plotFieldAtTime(float(time), fieldname,*settings)
            if (time=="0"):
                print("Dealing with time = 0")
                plotFieldAtInitialTime(fieldname, *settings)


def plotFieldAtTime(time, fieldname, isoFileNames, gridOption, lineX, lineY,xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, savePath = "default", figsize = None, logZAxis = False):
    timeSteps = getTimeSteps(".")
    nearestTime = getNearestTime(time, timeSteps)

    # deal with log file
    if ("log" in fieldname):
        x,y,z,field = createFields(nearestTime,fieldname.replace("log",""))
    # for field
    else:
        x,y,z,field = createFields(nearestTime, fieldname)
    
    # for contours
    isoXs, isoYs = createPhiChiContours(nearestTime, isoFileNames)
    if (savePath == "default"):
        savePath = "./postProcessing/foam2Columns/" + str(nearestTime) + "/" + fieldname + ".png"
    settings = [isoFileNames, gridOption, lineX, lineY, isoXs, isoYs, xticks, yticks, xlim, ylim, xname, yname, titlename, caxis, figsize, logZAxis]
    
    plotPureField(x, y, field, nearestTime, savePath ,*settings)


def plotPureField(x,y,field,timename,savePath, isoFileNames, gridOption, lineX, lineY, isoXs, isoYs, xticks, yticks, xlim, ylim, xname, yname, titlename,caxis,figsize = None, logZAxis = False):
    from matplotlib.ticker import StrMethodFormatter
    matplotlib.rcParams['mathtext.fontset'] = 'stix'
    matplotlib.rcParams['font.family'] = 'STIXGeneral'


    fig = plt.figure()

    if (figsize != None):
        fig.set_size_inches(figsize[0],figsize[1])

    print("min value{}".format(np.min(field)))
    
    # plot for the field
    if (logZAxis):
        field[field<1e-7]  = 1e-7
        if (np.min(field) < 10**(caxis[0]+0.1)):
            field[0] = 10**(caxis[0] + 0.1)
        im = plt.tricontourf(x,y,np.log10(field), 100, cmap = "hot")
        plt.colorbar()
        im.set_clim(caxis)
        
    else:
        im = plt.tricontourf(x,y,field,levels = 100, cmap = "hot")
        plt.colorbar()
        im.set_clim(caxis)



    # plot for the contour
    for isoFile in isoFileNames:
        plt.scatter(isoXs[isoFile], isoYs[isoFile],edgecolors = 'none', s = 0.1,label = isoFile)
    if (len(isoFileNames) > 0):
        plt.legend(markerscale = 10)

    # plot grids and a auxillary line to help further line sampling
    if (gridOption):
        plt.grid()
        plt.plot(lineX, lineY,"--", linewidth = 0.3)
    




    # cbarticks = np.arange(0,0.0031,0.001)
    # cbar = plt.colorbar(im, ticks = cbarticks)
    # cbar.ax.tick_params(labelsize = 15)


    plt.gca().xaxis.set_major_formatter(StrMethodFormatter('{x:,.2e}'))
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.2e}'))
    plt.tick_params(axis='both', which='major', labelsize=13)
    plt.xticks(xticks)
    plt.yticks(yticks)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.xlabel(xname,fontsize = 15)
    plt.ylabel(yname,fontsize = 15)
    plt.title(titlename + " at time = {}".format(timename), fontsize = 25)
    plt.tight_layout()

    plt.savefig(savePath,dpi=250)
    plt.clf()
    plt.close()

def getPhiZChiPath(time, filename):
    timeSteps = getTimeSteps(".")
    nearestTime = getNearestTime(time, timeSteps)
    path = "./postProcessing/" + filename + "/" + nearestTime + "/isoSurface.xy"
    return path

def createPhiChiContour(time, filename):
    path = getPhiZChiPath(time, filename)
    data = np.loadtxt(path, skiprows = 1)

    x = data[:,0]
    y = data[:,1]
    return x, y

def createPhiChiContours(time, filenames):
    x = {}
    y = {}
    for filename in filenames:
        path = getPhiZChiPath(time, filename)
        data = np.loadtxt(path, skiprows = 1)

        x[filename] = data[:,0]
        y[filename] = data[:,1]
    return x, y



def getFieldMinMaxAtTime(time, fieldname):
    timeSteps = getTimeSteps(".")
    nearestTime = getNearestTime(time, timeSteps)
    if (nearestTime!='0') or os.path.isfile("./0/" + fieldname):
        x,y,z,field = createFields(nearestTime, fieldname)
        min = np.min(field)
        max = np.max(field)
    else:
        min,max = 0,0
    print("min = {}".format(min))
    print("max = {}".format(max))
    return min, max

def getFieldMinMaxAtAllTimes(fieldname):
    timeSteps = getTimeSteps(".")
    min = []
    max = []
    for time in timeSteps:
        print("Dealing with time = {}".format(time))
        tempmin,tempmax = getFieldMinMaxAtTime(float(time), fieldname)
        min.append(tempmin)
        max.append(tempmax)

    minvalue = np.min(min)
    maxvalue = np.max(max)
    with open("minMaxFields.txt",'a') as myfile:
        myfile.write("field {}:  min value: {}  max value {} \n".format(fieldname, minvalue, maxvalue))
    return min, max

def getFieldMinMaxAtSelectedTimes(fieldname, startTime, endTime):
    timeSteps = getTimeSteps(".")
    min = []
    max = []

    for time in timeSteps:
        if ((float(time)>startTime) and (float(time)<endTime)):
            print("Dealing with time = {}".format(time))
            tempmin,tempmax = getFieldMinMaxAtTime(float(time), fieldname)
            min.append(tempmin)
            max.append(tempmax)

    minvalue = np.min(min)
    maxvalue = np.max(max)
    with open("minMaxFields.txt",'a') as myfile:
        myfile.write("field {}:  min value: {}  max value {} \n".format(fieldname, minvalue, maxvalue))
    return min, max

def getSelectedTimeSteps(startTime, endTime):
    timeSteps = getTimeSteps(".")
    timeSteps = [float(t) for t in timeSteps if ((float(t)<endTime) and (float(t)>startTime))]
    return timeSteps

def getFieldsMaxAtSelectedTimes(fieldnames, startTime, endTime, logname):
    returnDict = {}
    timeSteps = getSelectedTimeSteps(startTime, endTime)
    if (len(timeSteps) == 0):
        print("Nothing to deal with!")
        return returnDict
    
    for field in fieldnames:
        print("Dealing with Species {}".format(field))
        minArray, maxArray = getFieldMinMaxAtSelectedTimes(field, startTime, endTime)
        returnDict[field] = maxArray
    
    with open(logname,'w') as myfile:
        # write title
        title = "# time "
        for field in fieldnames:
            title += field + " "
        myfile.write(title + "\n")
        
        # write each field
        timeSteps = getSelectedTimeSteps(startTime, endTime)
        for i in range(len(timeSteps)):
            info = str(timeSteps[i]) + " "
            for field in fieldnames:
                info += str(returnDict[field][i]) + " "
            myfile.write(info + "\n") 
    return returnDict

def getGIFForField(fieldname, startTime, endTime, fps):
    timeSteps = getTimeSteps(".")
    image_list = []
    for timeStep in timeSteps:
        if ((float(timeStep) < endTime) and (float(timeStep) > startTime)) :
            path = "./postProcessing/foam2Columns/"+timeStep+"/"+fieldname + ".png"
            im = Image.open(path)
            image_list.append(im)
    image_list[0].save(fieldname + '.gif', save_all=True, append_images=image_list[1:], duration=1000/fps, loop=0)



def getGIFAtSelectedTimesForField(fieldname, startTime, endTime, fps):
    timeSteps = getTimeSteps(".")
    image_list = []
    for timeStep in timeSteps:
        if ((float(timeStep)>startTime) and (float(timeStep)<endTime)):
            path = "./postProcessing/foam2Columns/"+timeStep+"/"+fieldname + ".png"
            im = Image.open(path)
            image_list.append(im)
    image_list[0].save(fieldname + '.gif', save_all=True, append_images=image_list[1:], duration=1000/fps, loop=0)

def getGatheredGIFForField(path, savePath, startTime, endTime, fps):
    timeSteps = getPngTimeSteps(path)
    image_list = []
    for timeStep in timeSteps:
        if ((float(timeStep) < endTime) and (float(timeStep) > startTime)) :
            imagepath = path + "/" + timeStep + ".png"
            im = Image.open(imagepath)
            image_list.append(im)
    image_list[0].save(savePath + '.gif', save_all=True, append_images=image_list[1:], duration=1000/fps, loop=0)

    
