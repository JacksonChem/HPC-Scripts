#!/tools/python-3.9.2/bin/python

#******************************************************#
#                                                      #
#           Script for calculating band gaps           #
#           from Quantum Espresso .dat files           #
#                                                      #
#        Benjamin A Jackson,  Auburn University        #
#                  baj0040@auburn.edu                  #
#                                                      #
#                 Updated:  06/03/2022                 #
#                                                      #
#******************************************************#

import os
import sys
import numpy as np
import argparse

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--SpinPol', '-s', action="extend",              # Specify spin-polarized bands; requires 2 .dat files
	                    type=str, nargs=2, dest='fileList')              #
	parser.add_argument('--Unpol', '-u', type=str, dest='fileName')      # Specify unpolarized bands; requires 1 .dat file
	parser.add_argument('--EFermi', '-e', type=float)                    # Explicitly state eFermi
	parser.add_argument('--FileNscf', '-f', type=str, default=None)	     # Explicitly state the NSCF file
	parser.add_argument('--UseNscfFromBand', '-n', action="store_true")	 # Use band filename to read matching nscf file; {filename}.nscf.out
	parser.add_argument('--Threshold', '-t', type=float,default=2.0)	   # Threshold +/-(eV) about the eFermi to check for band gap
	args=parser.parse_args() 
	#Section for handling where eFermi is obtained
	if args.UseNscfFromBand :          # Use band file name to get nscf name, assume nscf ends in *.nscf.out
		if args.fileName is not None :   # If unpolarized is specified
			fermiFile = bandNameConverter(args.fileName)
		elif args.fileList is not None : # If spin polarized is used
			fermiFile = bandNameConverter(args.fileList[0])
		fileChecker(fermiFile)           # Check if NSCF file exists
		eFermi=fermiFromNscf(fermiFile)  # Obtain Fermi Energy from NSCF file
	elif args.FileNscf is not None :   # If NSCF file is specified
		fermiFile=args.FileNscf
		fileChecker(fermiFile)
		eFermi=fermiFromNscf(fermiFile)
	else : 
		if args.EFermi == None :        # Check if eFermi is specified with -e
			exit("No Fermi Energy was specified")
		else :
			eFermi=args.EFermi            # Assign eFermi
	# Section for calculating the band gap	
	thresh=args.Threshold             # Variable for +/- threshold to search around eFermi for bandgap
	if args.fileName is not None :    # Spin unpolarized method 
		fileChecker(args.fileName)
		bandMat=readBands(args.fileName,eFermi)
	elif args.fileList is not None :  # Spin polarized method
		fileChecker(args.fileList[0]); fileChecker(args.fileList[1])
		bandMat1=readBands(args.fileList[0],eFermi)
		bandMat2=readBands(args.fileList[1],eFermi)
		bandMat=joinBands(bandMat1, bandMat2)
	print("The direct band gap is: ", directBandGap(bandMat,thresh))
	print("The indirect band gap is: ", indirectBandGap(bandMat,thresh))

#=======================================#
# Check if files exist
def fileChecker(fileName) :
	try :
		if os.path.exists(os.path.join(os.getcwd(), fileName)) is False :
			raise FileNotFoundError
	except FileNotFoundError :
		exit("ERROR: The file" + fileName + " was not found in the current directory.")

#=======================================#
# Functions for getting NSCF file name and getting eFermi from NSCF
def bandNameConverter(bandFile) : # Converts {name}.band[1,2].dat to {name}.nscf.out
	fermiFile=bandFile.split(".")[0]
	return (fermiFile + ".nscf.out")
def fermiFromNscf(NscfFile) :
	with open(NscfFile, "r") as file :
		for line in file :
			if "the Fermi energy is" in line :
				eFermi = float(((line.replace("the Fermi energy is","")).replace("ev","")).strip())
	return eFermi
#=======================================#
#Section for reading and editting bands
def readBands(fileName, eFermi):
	with open(fileName, "r") as file:
		i = 0		# tracks line number
		kP = -1 # tracks specific k-point
		for line in file:
			if i == 0 : # Read initial line
				nBnds = int(line.split()[2][:-1])     # Number of bands
				nKPoints = int(line.split()[4])			 	# Number of k-points
				bandMat = np.zeros((nBnds, nKPoints))	#	Matrix to store bands
				kMat = np.zeros((nKPoints,3))         # Matrix to store k points
			elif len(line.split()) == 3 :           # Track k points
				kP += 1
				#kMat[kP,0],kMat[kP,1],kMat[kP,2] = line.split()[0],line.split()[1],line.split()[2]
				bN = 0
			else :
				line = line.split()
				for band in line :
					bandMat[bN,kP] = float(band) - eFermi
					bN += 1
			i += 1
	return bandMat
def joinBands(bandMat1,bandMat2) : #Join two bands matrices column-wise
	newBandMat=np.append(bandMat1,bandMat2,axis=1)
	return newBandMat
#=======================================#
#Section for calculation band gaps
def directBandGap(bandMat,thresh) :
	bandGap=999999
	for i in range(len(bandMat[0])) : #Columns
		band1=condBandMin(bandMat[:,i],thresh)
		band2=valBandMax(bandMat[:,i],thresh)
		newBandGap=band1-band2
		if newBandGap < bandGap :
			bandGap=newBandGap
	return bandGap
def condBandMin(array,thresh) : # Find minimum of conduction bands in range from eFermi to +Threshold
	smallest=99999
	for i in array :
		if i > 0 and i < (0 + thresh) and i < smallest :
			smallest=i	
	return smallest
def valBandMax(array,thresh) : # Find maximum of valence bands in range from eFermi to -Threshold
	biggest=-99999
	for i in array :
		if i < 0 and i > (0 - thresh) and i > biggest :
			biggest=i	
	return biggest
def indirectBandGap(bandMat,thresh) :
	bandGap=999999
	valMax=-99999
	conductMin=99999
	for i in range(len(bandMat[0])) :
		for j in range(len(bandMat)) :
			#Find minimum of all conduction bands
			if bandMat[j,i] > 0 and bandMat[j,i] < (0 + thresh) and bandMat[j,i] < conductMin :
				conductMin = bandMat[j,i] 
			#Find maximum of all valence bands
			if bandMat[j,i] < 0 and bandMat[j,i] > (0 - thresh) and bandMat[j,i] > valMax :
				valMax = bandMat[j,i] 
	return (conductMin - valMax)
#=======================================#

main()



