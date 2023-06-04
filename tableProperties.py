import numpy as np
import matplotlib.pyplot as plt
from readOFFiles import readOFScalarList

class FGMtableProperties:
    # ----- Data member ----- #
    #- 1) tableRoute
    #- 2) Zgrid
    #- 3) Cgrid
    #- 4) outputFieldsList (e.g. H2 O2 C7H16 in string)

    # ----- Function member ----- #
    # --- construcctor --- #
    def __init__(self, tableRoute, Zgrid, Cgrid, outputFieldsList):
        self.tableRoute = tableRoute
        self.Zgrid      = Zgrid
        self.Cgrid      = Cgrid
        self.outputFieldsList = outputFieldsList

    # --- overloaded operators --- #
    def __call__(self):
        for field in self.outputFieldsList:
            field = field.replace("thermo:", "")
            if (field == "PVMax"):
                field = "PVmax"
            if (field == "PVMin"):
                field = "PVmin"
            self.drawField(field)

    # --- other functions --- #
    def drawField(self, fieldname):
        Z = self.Zgrid
        C = self.Cgrid
        ZZ, CC = np.meshgrid(Z, C)

        field = readOFScalarList(fieldname + "_table", self.tableRoute)
        field = np.array(field["data"]).reshape(len(Z), len(C)).transpose()
        plt.pcolor(ZZ,CC,field,cmap = "hot")
        plt.xlabel("Z")
        plt.ylabel("C")
        plt.title(fieldname)
        plt.colorbar()
        plt.savefig(self.tableRoute + fieldname + ".png", dpi = 150)
        plt.clf()
        plt.close()




