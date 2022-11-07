#!/tools/python-3.9.2/bin/python
#!/tools/python-3.9.2/bin/python


import math
import numpy as np
import argparse
import re
import os
import sys


def main():
    """
    This is a python script. You should write a real doc-string when your brain isn't of the fog.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--CellFileSuffix', '-C', type=str, default="-1.cell")
    parser.add_argument('--PosFileSuffix', '-P', type=str, default="-pos-1.xyz")
    parser.add_argument('--CellFile', type=str, default=None)
    parser.add_argument('--PosFile', type=str, default=None)
    parser.add_argument('--RadialCutOff', '-r', type=float, default=7.0)
    parser.add_argument('--Resolution', '-R', type=int, default=300)
    parser.add_argument('--StepStart', '-S', type=int, default=1)
    parser.add_argument('--StepSkip', '-s', type=int, default=0)
    parser.add_argument('--DynamicCell', '-D', action='store_true')
    parser.add_argument('--ElementsAnalyzed', '-E', default="ALL",
                        help='comma separated last of element indices (repeated adjacent elements are grouped)')
    parser.add_argument("ProjectName", type=str)
    args = parser.parse_args()
    x = re.search(r'(.*)(.out|.inp|-pos-1.xyz|-1.cell)', args.ProjectName)
    if x:
        projectName = x.group(1)
    else:
        projectName = args.ProjectName

    if args.CellFile is None:
        if x:
            cellFile = x.group(1) + args.CellFileSuffix
        else:
            cellFile = args.ProjectName + args.CellFileSuffix
    else:
        cellFile = args.CellFile
    if args.PosFile is None:
        if x:
            posFile = x.group(1) + args.PosFileSuffix
        else:
            posFile = args.ProjectName + args.PosFileSuffix
    else:
        posFile = args.PosFile
    ErrorHandler(posFile, cellFile)
    Trajectory(projectName, posFile, cellFile, args.StepStart, args.StepSkip, args.DynamicCell, args.RadialCutOff,
               args.Resolution)


def ErrorHandler(posFile, cellFile):
    try:
        if os.path.exists(os.path.join(os.getcwd(), posFile)) is False:
            raise FileNotFoundError
    except FileNotFoundError:
        exit("The POS file "+posFile+" was not found in the current directory.")
    try:
        if os.path.exists(os.path.join(os.getcwd(), cellFile)) is False:
            raise FileNotFoundError
    except FileNotFoundError:
        exit("The cell file "+cellFile+" was not found in the current directory.")


def radDistroPrinter(projectName, data):
    with open(projectName + '.rdis', 'w') as file:
        sys.stdout = file
        formatString = '{i:^15}'
        print('{0:^15}{1:^15}{2:^15}{3:^15}{4:^15}{5:^15}{6:^15}'.format("[Radius (A)]", "[Intensity]",
                                                                         "[Intensity]", "[Intensity]",
                                                                         "[Intensity]", "[Intensity]",
                                                                         "[Intensity]"))
        for i in range(len(data)):
            print('{0:^15f}{1:^15f}{2:^15f}{3:^15f}{4:^15f}{5:^15f}{6:^15f}'.format(data[i, 0], data[i, 1],
                                                                                    data[i, 2], data[i, 3],
                                                                                    data[i, 4], data[i, 5],
                                                                                    data[i, 6]))


class Trajectory:
    def __init__(self, projectName, posFile, cellFile, stepStart, skip, dynamicDim, radCutOff, radRes):
        self.posFile = posFile
        self.cellFile = cellFile
        self.skip = skip + 1
        self.stepStart = stepStart
        #if stepStart == 0:
        #    self.stepStart = stepStart
        #else:
        #    self.stepStart = stepStart - 1
        self.radRes = radRes
        self.radCutOff = radCutOff
        self.dynamicDim = dynamicDim
        self.shellVol = self.shellVolCalc()
        self.numAtoms, self.nSteps, self.atomList, self.coords = self.posReader(posFile)
        self.cellVol, self.cellParam = self.cellReader(cellFile)
        self.groups, self.nGroups = self.groupLabels()
        self.radDisFin = self.couplerFunction()
        radDistroPrinter(projectName, self.radDisFin)

    def posReader(self, posFile):
        with open(posFile, 'r') as file:
            data = file.readlines()
        numAtoms = int(data[0].split()[0])
        stepsTot = int(len(data) / (numAtoms + 2))
        nSteps = (stepsTot - self.stepStart) // self.skip
        atomList = [line.split()[0] for line in data[2:numAtoms + 2]]
        coordsFull = np.zeros((nSteps, numAtoms, 3))
        for step in range(nSteps):
            coordsStep = np.zeros((numAtoms, 3))
            readStart = step * self.skip * (numAtoms + 2) + self.stepStart * self.skip * (numAtoms + 2)
            for j, line in enumerate(data[readStart + 2:readStart + numAtoms + 2]):
                coordsStep[j, :] = [float(value) for value in line.split()[1:]]
            coordsFull[step] = coordsStep
        return numAtoms, nSteps, atomList, coordsFull

    def cellReader(self, cellFile):
        with open(cellFile, 'r') as file:
            cellData = file.readlines()
        if not self.dynamicDim:
            params = [float(value) for value in cellData[1].split()]
            cellVol = params[-1]
            for i in [0, 0, -1]:
                del params[i]
            cellParam = np.reshape(params, (3, 3))
        else:
            cellData = np.delete(cellData, 0, axis=0)
            cellParam = np.zeros((self.nSteps, 3, 3))
            cellVol = np.zeros(self.nSteps)
            for step in range(self.stepStart, self.nSteps, self.skip):
                params = cellData[step].split()
                cellVol[step] = params[-1]
                for i in [0, 0, -1]:
                    del params[i]
                cellParam[step] = np.reshape(params, (3, 3))
        return cellVol, cellParam

    def groupLabels(self):
        groups = np.zeros(len(self.atomList))
        atomTag = "XX"
        groupCount = 0
        for i, atom in enumerate(self.atomList):
            if atomTag == atom:
                groups[i] = groupCount
            else:
                atomTag = atom
                groupCount += 1
                groups[i] = groupCount
        nGroups = int(max(groups))
        return groups, nGroups

    def couplerFunction(self):
        totCouples = int(self.nGroups * (self.nGroups + 1) / 2)
        radDisFn = np.zeros((self.radRes, 1 + totCouples))
        dr = self.radCutOff / float(self.radRes)
        for i in range(0, self.radRes):
            radDisFn[i, 0] = (i + 1) * dr
        radDisFn = radDisFn.transpose()
        pairNum = 1
        j = 1
        for group1 in range(1, self.nGroups + 1):
            for group2 in range(j, self.nGroups + 1):
                radDisFn[pairNum] = self.calcRadDis(group1, group2)
                pairNum += 1
            j = j + 1
        return radDisFn.transpose()

    def calcRadDis(self, group_id1, group_id2):
        dr = self.radCutOff / float(self.radRes)
        radDis = np.zeros(self.radRes)
        for step in range(0, self.nSteps - 1):
            dataGroup1 = []
            dataGroup2 = []
            for j, coords1 in enumerate(self.coords[step]):
                if self.groups[j] == group_id1:
                    dataGroup1.append(coords1)
            for k, coords2 in enumerate(self.coords[step]):
                if self.groups[k] == group_id2:
                    dataGroup2.append(coords2)
            for n, atom1 in enumerate(dataGroup1):
                for m, atom2 in enumerate(dataGroup2):
                    dis0 = math.dist(atom1, atom2)
                    disAplus = math.dist(atom1, np.add(atom2, self.cellParam[0]))
                    disAmin = math.dist(atom1, np.subtract(atom2, self.cellParam[0]))
                    disBplus = math.dist(atom1, np.add(atom2, self.cellParam[1]))
                    disBmin = math.dist(atom1, np.subtract(atom2, self.cellParam[1]))
                    disCplus = math.dist(atom1, np.add(atom2, self.cellParam[2]))
                    disCmin = math.dist(atom1, np.subtract(atom2, self.cellParam[2]))
                    for dist in [dis0, disAplus, disAmin, disBplus, disBmin, disCplus, disCmin]:
                        if 0 < dist < self.radCutOff:
                            binNum = int(dist / dr)
                            radDis[binNum] += 1
        if group_id1 == group_id2:
            atomNorm = len(dataGroup1) * (len(dataGroup1) - 1)
        else:
            atomNorm = len(dataGroup1) * len(dataGroup2)
        for r in range(len(radDis)):
            if radDis[r] != 0.0:
                radDis[r] = radDis[r] * self.cellVol / self.shellVol[r] / self.nSteps / atomNorm
        return radDis

    def shellVolCalc(self):
        shellVol = np.zeros(self.radRes)
        dr = self.radCutOff / float(self.radRes)
        for r in range(self.radRes):
            shellVol[r] = 4 * math.pi * (r * dr) ** 2 * dr
        return shellVol


main()
