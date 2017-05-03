import numpy as np
import os
import cPickle as pickle

# set path according to location of the exported field from COMSOL
# sourceFolder = '/media/carl/4ECC-1C44/ComsolData/cuffFiner'
# sourceFolder = '/media/carl/4ECC-1C44/ComsolData/stimulationField/noCuffStimulation'
# sourceFolder = '/media/carl/18D40D77D40D5900/COMSOL_data/oil_sigma_0.0000001_contact_xP0'
# sourceFolder = '/media/carl/18D40D77D40D5900/COMSOL_data/oil_sigma_0.0000001_Oil5cm_xP0'
sourceFolder = '/Volumes/SANDISK/ComsolData/exportAgain/noCuff190Inner50Endoneurium'
# sourceFolder = '/Volumes/SANDISK/ComsolData/exportAgain/noCuff300Inner20Endoneurium'
# sourceFolder = '/Volumes/SANDISK/ComsolData/exportAgain/oil190Inner50Endoneurium'

# desired location and name of dictionary
destinationFolder = os.path.join(sourceFolder, 'numpy')

try:
    os.makedirs(destinationFolder)
except OSError:
    if not os.path.isdir(destinationFolder):
        raise

# axon positions
axonXs = [0.00023, 0.00024] # [0, 0.00009, 0.00018, 0.00027, 0.00036] # [0, 1000] #

def load_field(folder, axonXs):

        # get file names
        filenames = [f for f in sorted(os.listdir(folder)) if os.path.isfile(os.path.join(folder, f))]

        axonXSteps = len(axonXs)
        assert axonXSteps == len(filenames)

        # load each field (different axon positions)
        fields = []
        for filename in filenames:
            fields.append(np.loadtxt(os.path.join(folder, filename)))

        print 'loaded field'

        # get coordinates (should be equal for all field files, otherwise nothing works)
        x = fields[0][:, 0]
        y = fields[0][:, 1]
        z = fields[0][:, 2]

        # sort by coordinate values, x changing fastest, z slowest
        orderIndices = np.lexsort((x, y, z))
        x = x[orderIndices]
        y = y[orderIndices]
        z = z[orderIndices]

        # get coordinate values
        xValues = np.unique(x)
        yValues = np.unique(y)
        zValues = np.unique(z)

        # get number of steps
        xSteps = len(xValues)
        ySteps = len(yValues)
        zSteps = len(zValues)

        # voltages are different for each field
        voltages = []
        for i in range(axonXSteps):
            v = fields[i][:, 3]
            v = v[orderIndices]  # order voltages as well
            voltages.append(v)

        # transform data to 3D-field with integer indices replacing actual coordinate values
        fieldImage = np.zeros([xSteps, ySteps, zSteps, axonXSteps])

        for axonXInd in range(axonXSteps):
            for xInd in range(xSteps):
                for yInd in range(ySteps):
                    for zInd in range(zSteps):
                        vIndexCalc = xInd + xSteps * (yInd + zInd * ySteps)
                        fieldImage[xInd, yInd, zInd, axonXInd] = voltages[axonXInd][vIndexCalc]

        fieldDict = {'fieldImage': fieldImage,
                     'x': xValues,
                     'y': yValues,
                     'z': zValues,
                     'axonX': axonXs}

        return fieldDict


fieldDict = load_field(sourceFolder, axonXs)
np.save(os.path.join(destinationFolder, 'fieldDict.npy'), fieldDict)
