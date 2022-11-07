#!/tools/python-3.9.2/bin/python

import numpy as np
import argparse
import sys
import os
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--CellFileSuffix', '-C', type=str, default="-1.cell")
    parser.add_argument('--PosFileSuffix', '-P', type=str, default="-pos-1.xyz")
    parser.add_argument('--CellFile', type=str, default=None)
    parser.add_argument('--PosFile', type=str, default=None)
    parser.add_argument('--StepStart', '-S', type=int, default=1)
    parser.add_argument('--StepSkip', '-s', type=int, default=0)
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
    Trajectory(projectName, posFile, cellFile, args.StepSkip, args.StepStart)


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


class Trajectory:
    def __init__(self, projectName, posFile, cellFile, skip, stepStart):
        self.posFile = posFile
        self.cellFile = cellFile
        self.skip = skip + 1
        if stepStart == 0:
            self.stepStart = stepStart
        else:
            self.stepStart = stepStart - 1
        self.numAtoms, self.nSteps, self.atomList, self.coords = self.posReader()
        self.cellVol, self.cellParam = self.cellReader()
        self.filePrinter(projectName, self.cellParam, self.coords)

    def posReader(self):
        with open(self.posFile, 'r') as file:
            data = file.readlines()
        numAtoms = int(data[0].split()[0])
        stepsTot = int(len(data) / (numAtoms + 2))
        nSteps = (stepsTot - self.stepStart) // self.skip
        atomList = [line.split()[0] for line in data[2:numAtoms + 2]]
        coordsFull = np.zeros((nSteps, numAtoms, 3))
        for step in range(nSteps):
            coordsStep = np.zeros((numAtoms, 3))
            readStart = step * self.skip * (numAtoms + 2) + self.stepStart
            for j, line in enumerate(data[readStart + 2:readStart + numAtoms + 2]):
                coordsStep[j, :] = [float(value) for value in line.split()[1:]]
            coordsFull[step] = coordsStep
        return numAtoms, nSteps, atomList, coordsFull

    def cellReader(self):
        with open(self.cellFile, 'r') as file:
            cellData = file.readlines()
            cellData = np.delete(cellData, 0, axis=0)
        cellParam = np.zeros((self.nSteps, 3, 3))
        cellVol = np.zeros(self.nSteps)
        for step in range(self.stepStart, self.nSteps, self.skip):
            # Correction for when cell file has one fewer steps than pos
            if step > len(cellData)-1:
                params = cellData[step-1].split()
                cellVol[step] = params[-1]
                for i in [0, 0, -1]:
                    del params[i]
                cellParam[step] = np.reshape(params, (3, 3))
            else:
                params = cellData[step].split()
                cellVol[step] = params[-1]
                for i in [0, 0, -1]:
                    del params[i]
                cellParam[step] = np.reshape(params, (3, 3))
        return cellVol, cellParam

    def filePrinter(self, projectName, cellParam, coords):
        with open(projectName+'.axsf', 'w') as file:
            sys.stdout = file
            print("  ANIMSTEPS    ", self.nSteps)
            print("  CRYSTAL")
            for step in range(self.nSteps):
                print("  PRIMVEC     ", step+1)
                for j in range(0, 3):
                    print('{0: ^15f}{1: ^15f}{2: ^15f}'.format(cellParam[step, j, 0], cellParam[step, j, 1],
                                                               cellParam[step, j, 2]))
                print("  PRIMCOORD   ", step+1)
                print("  ", self.numAtoms, "    1")
                for k in range(len(coords[0])):
                    print('{0:<4}{1:-15f}{2:-15f}{3:-15f}'.format(self.atomList[k], coords[step, k, 0],
                                                                     coords[step, k, 1], coords[step, k, 2]))


if __name__ == '__main__':
    main()

