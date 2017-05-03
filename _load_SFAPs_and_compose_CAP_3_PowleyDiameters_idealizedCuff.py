import cPickle as pickle
import os
import numpy as np
import matplotlib as mpl
mpl.use('TKAgg')
import matplotlib.pyplot as plt


import matplotlib.cm as cm
import matplotlib.colors as colors

CBcolors = np.array(((0.,0.,0.), (230., 159., 0.), (86., 180., 233.), (0., 158., 115.)))/255

# saveDict = pickle.load(open(os.path.join('/media/carl/4ECC-1C44/PyPN/SFAPs', 'SFAPsOil.dict'), "rb" )) # thinnerMyelDiam
saveDict = pickle.load(open(os.path.join('SFAPs', 'SFAPsPowleyMyelAsRecordingsIdealizedCuff4.dict'), "rb" )) # originalMyelDiam #/Volumes/SANDISK/PyPN/


# saveDict = {'unmyelinatedDiameters' : diametersUnmyel,
#             'unmyelinatedSFAPsHomo': [],
#             'unmyelinatedSFAPsFEM': [],
#             'unmyelinatedCV' : [],
#             't': [],
#             'myelinatedDiameters': diametersMyel,
#             'myelinatedSFAPsHomo': [],
#             'myelinatedSFAPsFEM': [],
#             'myelinatedCV' : [],
#             }

from scipy.signal import butter, lfilter, freqz

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

# parameters
lengthOfRecording = 200 #ms
dt = 0.0025 #ms
nRecording = int(lengthOfRecording/dt)
tArtefact = 0.1 # ms
nArtefact = tArtefact/dt

electrodeDistance = 70.*1.2 #*1.5 # 70. # mm
jitterAmp = 5 #ms
jitterDist = 0.1*electrodeDistance # 0.03
numMyel = 200
numUnmyel = 2000 # 350
poles = 2
poleDistance = 3 # 1 # mm
polePolarities = [1, -1]
fieldTypes = [0, 1] # 0: homo, 1: FEM

stringsDiam = ['unmyelinatedDiameters', 'myelinatedDiameters']
stringsSFAPHomo = ['unmyelinatedSFAPsHomo', 'myelinatedSFAPsHomo']
stringsSFAPFEM = ['unmyelinatedSFAPsFEM', 'myelinatedSFAPsFEM']
stringsSFAPIdeal = ['unmyelinatedSFAPIdeal', 'myelinatedSFAPIdeal']
stringsCV = ['unmyelinatedCV', 'myelinatedCV']
# tHomo = saveDict['t']
ts = [np.arange(0,100.0025,0.0025), np.arange(0,20.0025,0.0025)]

wantedNumbersOfFibers = [(0.0691040631732923, 0.182192465406599, 0.429980837522710, 0.632957475186409, 2.05015339910575,
                          3.10696898591111,  4.54590886074274,  7.22064649366380,  7.60343269800399,  8.61543655035694,
                          8.07683524571988,  7.15617584468796,  7.04457675416097,  6.77590492234067,  5.67583310442061,
                          5.20464797635635,  3.22856301277829,  2.51011904564906,  2.06140597644239,  1.50026642131635,
                          1.32118496258518,  0.849999834520921, 0.760773515404445, 0.312027350382088, 0.200593738933586,
                          0.201222559431810, 0.15, 0.1),
                         (0.6553, 0.658, 2.245, 2.282, 4.627, 4.665, 16.734, 16.737, 19.393, 19.396, 17.776, 17.779,
                          15.503, 15.506, 9.26, 9.234, 5.993, 5.961, 2.272, 2.275, 2.138, 2.106, 1.734, 1.634, 1.151,
                          1.189, 0.948, 0.917, 2.1, 2.1)]

diametersMyel = np.array(saveDict[stringsDiam[1]])
sigma = .5 # 0.3 # 0.25
mu = 2.3 # .7
wantedNumbersOfFibers[1] =  1/(sigma * np.sqrt(2 * np.pi)) *np.exp( - (diametersMyel - mu)**2 / (2 * sigma**2) )

# plt.plot(diametersMyel, wantedNumbersOfFibers[1])
# plt.title('Myelinated fiber diameter distribution')
# plt.ylabel('probability density')
# plt.xlabel('diameter in $\mu$m')
# plt.show()

wantedNumbersOfFibers[0] = np.divide(wantedNumbersOfFibers[0],  np.sum(wantedNumbersOfFibers[0]))*numUnmyel
wantedNumbersOfFibers[1] = np.divide(wantedNumbersOfFibers[1],  np.sum(wantedNumbersOfFibers[1]))*numMyel

# -------------------- plot recorded data ---------------------------------
import testWaveletDenoising as w
data = np.loadtxt('experimentalData/SD_1ms_AllCurrents.txt')
denoisedVoltage = w.wden(data[:,1], level=12, threshold=1.) # data[:,1] #w.wden(data[:,1], level=12, threshold=1.5) # data[:,1] #

tStart = 3.026 # 3.0245
time = data[:,0]
tCut = (time[time>tStart] - tStart)*1000
vDenCut = denoisedVoltage[time>tStart]/1000

vDenCutMax = np.max(vDenCut[tCut>4])

plt.plot(tCut, vDenCut, color='black', linewidth=1, label='Experimental data')

def shift_signal(signal, difference, length):

    # make peak come earlier
    if difference > 0:
        paddedSignal = signal[difference:]
    else:
        paddedSignal = np.concatenate((np.zeros(int(np.abs(difference))), signal))

    if len(paddedSignal) < length:
        paddedSignal = np.concatenate((paddedSignal, np.zeros(length - len(paddedSignal))))
    else:
        paddedSignal = paddedSignal[:length]

    return paddedSignal


tCAP = np.arange(0,lengthOfRecording,0.0025)

fieldStrings = ['Homogeneous', 'FEM', 'Ideal Cuff']
for fieldTypeInd in [2,1,0]: # fieldTypes:

    CAP = np.zeros(nRecording)
    CAPSmoothed = np.zeros(nRecording)

    for typeInd in [0,1]:

        diameters = np.array(saveDict[stringsDiam[typeInd]])
        CVs = np.array(saveDict[stringsCV[typeInd]])
        t = ts[typeInd]
        numFibers = len(diameters)

        # wanted number of fibers per diameter
        # wantedNums = np.ones(numFibers)*1000
        wantedNums = wantedNumbersOfFibers[typeInd]

        if fieldTypeInd == 0:
            SFAP = np.transpose(np.array(saveDict[stringsSFAPHomo[typeInd]]))
        elif fieldTypeInd == 1:
            SFAP = np.transpose(np.array(saveDict[stringsSFAPFEM[typeInd]]))
        else:
            SFAP = np.transpose(np.array(saveDict[stringsSFAPIdeal[typeInd]]))

        # plt.figure()
        # plt.plot(SFAP)
        SFAPNoArt = SFAP [t > tArtefact, :]

        # plt.figure()
        # plt.plot(SFAPNoArt[:,-1])
        # plt.show()

        for fiberInd in range(numFibers):

            currentSFAP = SFAPNoArt[:, fiberInd]

            # plt.plot(currentSFAP)
            # plt.show()

            if typeInd == 0:
                currentSFAP = currentSFAP[3000:]



            # caution, convolving!
            sigma = 0.6
            gx = np.arange(-3 * sigma, 3 * sigma, dt)
            gaussian = np.exp(-(gx / sigma) ** 2 / 2)
            # gaussianN = gaussian/np.sum(gaussian)
            # print np.sum(gaussian)
            smoothedSFAP = np.convolve(currentSFAP, gaussian, mode="same")

            # first find maximum position in signal
            peakInd = np.argmax(currentSFAP)

            # plt.plot(diameters, CVs)
            # plt.show()
            if typeInd == 1:
                # g_ratio = 0.6
                CV = 5*diameters[fiberInd] # *g_ratio # CVs[fiberInd]
            else:
                CV = np.sqrt(diameters[fiberInd]) * 2 * 0.7

            # print 'diameter : ' + str(diameters[fiberInd]) + 'CV = ' + str(CV)

            for ii in range(int(wantedNums[fiberInd])): # range(int(max(wantedNums[fiberInd], 1))):


                signalBothPoles = np.zeros(nRecording)
                jitterTemp = np.random.uniform(0, 1) * jitterDist
                for poleInd in range(poles):

                    # wantedPeakInd = (electrodeDistance + poleInd*poleDistance) / CV / dt + jitterAmp*np.random.uniform(-1,1) / dt
                    wantedPeakInd = (electrodeDistance + poleInd * poleDistance + jitterTemp) / CV / dt
                    # wantedPeakInd = 10/dt


                    difference = peakInd - wantedPeakInd

                    # plt.figure()
                    # plt.plot(currentSFAP)
                    # plt.show()

                    paddedSignal = shift_signal(currentSFAP, difference, nRecording)
                    paddedSignalSmoothed = shift_signal(smoothedSFAP, difference, nRecording)

                    signalBothPoles = np.add(signalBothPoles, polePolarities[poleInd] * paddedSignal)

                    # plt.plot(currentSFAP)
                    # plt.plot(paddedSignal)
                    # plt.show()

                # plt.plot(signalBothPoles)
                # plt.show()

                CAP = np.add(CAP, signalBothPoles)
                    # CAPSmoothed = np.add(CAPSmoothed, polePolarities[poleInd] * paddedSignalSmoothed)

                    # plt.plot(paddedSignal)
                    # plt.title(str(diameters[fiberInd]))
                    # plt.show()

                #     plt.plot(tCAP, CAP, label=fieldStrings[fieldTypeInd])
                # plt.show()

    # plt.plot(tCAP, CAPSmoothed, label=fieldStrings[fieldTypeInd] + ' smoothed with sigma = ' + str(sigma) + ' ms')

    # unfilteredScaling = vDenCutMax/np.max(CAP)

    plt.plot(tCAP, CAP, label=fieldStrings[fieldTypeInd], color=CBcolors[fieldTypeInd+1])
    plt.title('Comparison between experimental data and simulation')
    plt.ylabel('$V_{ext}$ [mV]')

    # cutoff = 1000 # 2800/(2*np.pi)
    #
    # for order in [2,3]:
    #     filteredCAP = butter_lowpass_filter(CAP, cutoff, 1000./dt, order=order)
    #     # scaling = vDenCutMax / np.max(filteredCAP)
    #     # plt.plot(tCAP, filteredCAP*scaling, label='order='+str(order) + ' scaled by ' + str(scaling))
    #     plt.plot(tCAP, filteredCAP, label='order=' + str(order))


    # from scipy import signal
    #
    # b, a = signal.butter(4, 10 / (np.pi / dt), 'low', analog=False)
    #
    # # plt.figure()
    # # w, h = signal.freqz(b, a)
    # # plt.plot(w, 20 * np.log10(abs(h)))
    # # plt.xscale('log')
    # # plt.title('Butterworth filter frequency response')
    # # plt.xlabel('Frequency [radians / second]')
    # # plt.ylabel('Amplitude [dB]')
    # # plt.margins(0, 0.1)
    # # plt.grid(which='both', axis='both')
    # # # plt.axvline(100, color='green')  # cutoff frequency
    # # plt.show()
    #
    # y = signal.filtfilt(b, a, CAP)
    # plt.plot(tCAP, y)

    # timesTicks = np.arange(5, int(max(tCAP)), 5)
    # tickLabelStrings = []
    # for tickTime in timesTicks:
    #     tickLabelStrings.append('%2.3f' % (electrodeDistance / tickTime))
    #
    # plt.xticks(timesTicks, rotation='vertical')
    # plt.gca().set_xticklabels(tickLabelStrings)
    # plt.xlabel('conduction velocity [m/s]')
    plt.xlabel('time [ms]')

# plt.grid()
plt.legend()

xlimits = ([0,120], [10,25], [30,100])
figureNames = ['CAPfull.eps', 'CAPmyel.eps', 'CAPunmyel.eps']
for limInd in range(3):
    plt.xlim(xlimits[limInd])
    if limInd == 2:
        plt.ylim((-0.01, 0.01))
    # plt.ylim(ylimits[axInd])
    # axarr[axInd].axis('equal')

    # plt.axes().set_aspect('equal', 'datalim')
    plt.savefig(os.path.join('/home/carl/Dropbox/_Exchange/Project/PyPN Paper/PythonFigureOutput', figureNames[limInd]),
            format='eps', dpi=300)

plt.show()

# jet = plt.get_cmap('jet')
# cNorm = colors.Normalize(vmin=0, vmax=numFibers - 1)
# scalarMap = cm.ScalarMappable(norm=cNorm, cmap=jet)
#
# for fiberInd in range(numFibers):
#     colorVal = scalarMap.to_rgba(fiberInd)
#
#     plt.plot(t[t>tArtefact], SFAP[t>tArtefact, fiberInd], color=colorVal)
# plt.show()