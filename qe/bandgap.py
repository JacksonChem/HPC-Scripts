#!/tools/python-3.9.2/bin/python

# ******************************************************#
#                                                       #
#           Script for calculating band gaps            #
#           from Quantum Espresso .dat files            #
#                                                       #
#        Benjamin A Jackson,  Auburn University         #
#                  baj0040@auburn.edu                   #
#                                                       #
#                 Updated:  12/01/2022                  #
#                                                       #
# ******************************************************#

import os
import numpy as np
import argparse
import shutil
import re


def main():
    bandMat = []
    eFermi = 999999
    fermiFile = None
    direct_gap = 0
    indirect_gap = 0
    parser = argparse.ArgumentParser()
    parser.add_argument('--SpinPol', '-s', action="extend",  # Specify spin-polarized bands; requires 2 .dat files
                        type=str, nargs=2, dest='fileList')
    parser.add_argument('--Unpol', '-u', type=str, dest='fileName')  # Specify unpolarized bands; requires 1 .dat file
    parser.add_argument('--EFermi', '-e', type=float)  # Explicitly state eFermi
    parser.add_argument('--FileNscf', '-f', type=str, default=None)  # Explicitly state the NSCF file
    parser.add_argument('--UseNscfFromBand', '-n',
                        action="store_true")  # Use band filename to read matching nscf file; {filename}.nscf.out
    parser.add_argument('--Threshold', '-t', type=float,
                        default=2.0)  # Threshold +/-(eV) about the eFermi to check for band gap, default 2 eV
    parser.add_argument('--fhi', '-a', type=str, dest='fhi_file', default=None)
    args = parser.parse_args()
    # Section for Quantum Espresso
    if args.fhi_file is None:
        # Section for handling where eFermi is obtained
        if args.UseNscfFromBand:  # Use band file name to get nscf name, assume nscf ends in *.nscf.out
            if args.fileName is not None:  # If unpolarized is specified
                # fermiFile = bandNameConverter(args.fileName)
                fermiFile = (args.fileName).split(".")[0] + ".nscf.out"
            elif args.fileList is not None:  # If spin polarized is used
                # fermiFile = bandNameConverter(args.fileList[0])
                fermiFile = (args.fileList[0]).split(".")[0] + ".nscf.out"
            fileChecker(fermiFile)  # Check if NSCF file exists
            eFermi = qe_fermiFromNscf(fermiFile)  # Obtain Fermi Energy from NSCF file
        elif args.FileNscf is not None:  # If NSCF file is specified
            fermiFile = args.FileNscf
            fileChecker(fermiFile)
            eFermi = qe_fermiFromNscf(fermiFile)
        else:
            if args.EFermi is None:  # Check if eFermi is specified with -e
                exit("No Fermi Energy was specified or no NSCF output file was specified")
            else:
                eFermi = args.EFermi  # Assign eFermi
        # Section for calculating the band gap
        if args.fileName is not None:  # Spin unpolarized method
            fileChecker(args.fileName)
            bandMat = qe_readBands(args.fileName, eFermi)
        elif args.fileList is not None:  # Spin polarized method
            fileChecker(args.fileList[0])
            fileChecker(args.fileList[1])
            bandMat1 = qe_readBands(args.fileList[0], eFermi)
            bandMat2 = qe_readBands(args.fileList[1], eFermi)
            bandMat = np.append(bandMat1, bandMat2, axis=0)  # Join matrices column wise
        else:
            exit("Something went wrong in the reading of your files.")

    # Section for FHI-aims
    elif args.fhi_file is not None:
        # Check for control.in and band files
        ctrl_file = (args.fhi_file).split(".")[0] + ".ctrl"
        band_file = (args.fhi_file).split(".")[0] + ".bands"
        geom_file = (args.fhi_file).split(".")[0] + ".geom"
        if os.path.exists(os.path.join(os.getcwd(), ctrl_file)) is not True:
            ctrl_file = "control.in"
        if os.path.exists(os.path.join(os.getcwd(), geom_file)) is not True:
            geom_file = "geometry.in"
        if os.path.exists(os.path.join(os.getcwd(), band_file)) is True:
            bandDir = fhi_expandBands(band_file, True)
        else:
            bandDir = os.getcwd()
            if os.path.exists(os.path.join(os.getcwd(), "band1001.out")) is False:
                exit("Error: band files were not found in the current directory.")
        bandMat = fhi_band(bandDir, ctrl_file, geom_file)
    else:
        exit("Error: Are you analyzing Quantum Espresso or FHI-aims output files?")

    direct_gap = bandGapCalc(bandMat, args.Threshold, True)
    indirect_gap = bandGapCalc(bandMat, args.Threshold, False)
    print("The direct band gap is: ", direct_gap)
    print("The indirect band gap is: ", indirect_gap)


def fileChecker(fileName):  # Check if files exist
    try:
        if os.path.exists(os.path.join(os.getcwd(), fileName)) is False:
            raise FileNotFoundError
    except FileNotFoundError:
        exit("ERROR: The file " + fileName + " was not found in the current directory.")


def bandGapCalc(bandMat, thresh, isDirect):
    valenceMax = -999999
    conductMin = 999999
    bandGap = 999999
    if isDirect:  # Calculate direct band gap
        for i in range(len(bandMat[0])):
            valMax = bandMinMax(bandMat[:, i], thresh, True)
            conMin = bandMinMax(bandMat[:, i], thresh, False)
            newBandGap = conMin - valMax
            if newBandGap < bandGap:
                bandGap = newBandGap
        return bandGap
    else:  # Calculate indirect band gap
        for i in range(len(bandMat[0])):
            newValMax = bandMinMax(bandMat[:, i], thresh, True)
            if newValMax > valenceMax:
                valenceMax = newValMax
            newConMin = bandMinMax(bandMat[:, i], thresh, False)
            if newConMin < conductMin:
                conductMin = newConMin
        return conductMin - valenceMax


def bandMinMax(array, thresh, isVal):
    smallest = 99999
    biggest = -99999
    if isVal:  # If true find the maximum of the valence bands
        for i in array:
            if 0 > i > (0 - thresh) and i > biggest:
                biggest = i
        return biggest
    else:  # Find the minimum of the conduction bands
        for i in array:
            if 0 < i < (0 + thresh) and i < smallest:
                smallest = i
        return smallest


def qe_fermiFromNscf(nscfFile):
    with open(nscfFile, "r") as file:
        for line in file:
            if "the Fermi energy is" in line:
                eFermi = float(((line.replace("the Fermi energy is", "")).replace("ev", "")).strip())
    return eFermi


def qe_readBands(fileName, eFermi):
    with open(fileName, "r") as file:
        i = 0  # tracks line number
        kP = -1  # tracks specific k-point
        for line in file:
            if i == 0:  # Read initial line
                nBnds = int(line.split()[2][:-1])  # Number of bands
                nKPoints = int(line.split()[4])  # Number of k-points
                bandMat = np.zeros((nBnds, nKPoints))  # Matrix to store bands
                # kMat = np.zeros((nKPoints, 3))  # Matrix to store k points
            elif len(line.split()) == 3:  # Track k points
                kP += 1
                # kMat[kP,0],kMat[kP,1],kMat[kP,2] = line.split()[0],line.split()[1],line.split()[2]
                bN = 0
            else:
                line = line.split()
                for band in line:
                    bandMat[bN, kP] = float(band) - eFermi
                    bN += 1
            i += 1
    return bandMat


def fhi_expandBands(bands_file, newDir):
    currDir = os.getcwd()
    if newDir:
        bandDir = os.path.join(currDir, bands_file.split(".")[0] + '_tmp')
        try:
            os.mkdir(bandDir)
        except OSError as error:
            exit(
                "The temp band dir " + bandDir + " already exists. Please remove from the current directory to proceed")
        # shutil.copy(file_baseName + ".ctrl", bandDir)
        # shutil.copy(file_baseName + ".geom", bandDir)
    elif not newDir:
        bandDir = currDir
    with open(bands_file, 'r') as collection:
        fileLines = []
        for line in collection:
            fileLines.append(line)
        i = 0
        while i <= (len(fileLines) - 1):
            if match := re.search('band[0-9]+\.out', fileLines[i]):
                fileName = match.group(0)
                i += 1
            else:
                with open(os.path.join(bandDir, fileName), 'w') as file:
                    while i <= (len(fileLines) - 1):  # True :
                        if match := re.search('band[0-9]+\.out', fileLines[i]):
                            break
                        file.write(fileLines[i])
                        i += 1
    return bandDir


def fhi_band(bandDir, ctrl_file, geom_file):
    latvec = []
    # Read geometry.in file
    for line in open(geom_file):
        line = line.split("#")[0]
        words = line.split()
        if len(words) == 0:
            continue
        if words[0] == "lattice_vector":
            if len(words) != 4:
                raise Exception(geom_file + ": Syntax error in line '" + line + "'")
            latvec += [np.array(list(map(float, words[1:4])))]
        if len(latvec) == 3:
            break
    if len(latvec) != 3:
        raise Exception(geom_file + ".geom: Must contain exactly 3 lattice vectors")
    latvec = np.asarray(latvec)
    rlatvec = []
    volume = (np.dot(latvec[0, :], np.cross(latvec[1, :], latvec[2, :])))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[1, :], latvec[2, :]) / volume))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[2, :], latvec[0, :]) / volume))
    rlatvec.append(np.array(2 * np.pi * np.cross(latvec[0, :], latvec[1, :]) / volume))
    rlatvec = np.asarray(rlatvec)
    max_spin_channel = 1
    band_segments = []
    band_totlength = 0.0  # total length of all band segments
    # Interpret input files
    for line in open(ctrl_file):
        words = line.split("#")[0].split()  # List of words in line,
        nline = " ".join(words)  # What is join doing?
        if nline.startswith("output band "):  # Read band lines
            if len(words) < 9 or len(words) > 11:  # 9 for end and start xyz, 11 for names of end and start
                raise Exception(ctrl_file + ": Syntax error in line '" + line + "'")
            start = np.array(list(map(float, words[2:5])))  # Get x y z of start
            end = np.array(list(map(float, words[5:8])))  # Get x y z of end
            length = np.linalg.norm(np.dot(rlatvec, end) - np.dot(rlatvec, start))  # Length of k-path
            band_totlength += length
            npoint = int(words[8])  # Number of points for that band
            band_segments += [(start, end, length, npoint)]
        elif nline.startswith("spin collinear"):
            max_spin_channel = 2
    nband = 0

    band_energies = []
    band_occupations = []
    band_energies2 = []
    band_occupations2 = []
    for i in band_segments:
        nband += 1
        file = "band1%03i.out" % nband
        for line in open(os.path.join(bandDir, file)):
            words = line.split()
            band_occupations += [list(map(float, words[4::2]))]
            band_energies += [list(map(float, words[5::2]))]
        if max_spin_channel == 2:
            file = "band2%03i.out" % nband
            for line in open(os.path.join(bandDir, file)):
                words = line.split()
                band_occupations2 += [list(map(float, words[4::2]))]
                band_energies2 += [list(map(float, words[5::2]))]
    if max_spin_channel == 2:
        band_energies = np.append(band_energies, band_energies2, axis=1)
    else:
        band_energies = np.asarray(band_energies)
    band_energies = band_energies.transpose()
    if bandDir != os.getcwd():
        shutil.rmtree(bandDir)  # Delete band directory if a new directory was created
    return band_energies


main()
