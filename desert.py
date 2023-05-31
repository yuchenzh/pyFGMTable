import numpy as np
def isnum(a):
    try:
        float(a)
        return True
    except:
        return False