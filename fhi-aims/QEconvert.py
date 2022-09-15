#!/tools/python-3.9.2/bin/python

#Assign the filename
import math
import os
import sys
import numpy as np
import re
	
#=======================================#	
def main() :
	fileName,baseName = FileChecker()#Error_Checker
	#Call function for intrepreting the QE input file
	ibravType, paramType, geomType, Geom, KPath, k_Check, CellParam = FileHandler(fileName)
	Geom = np.genfromtxt(fname=Geom, dtype=None, encoding=None)
	GeomMatIn = GeomHandler(Geom, geomType)
	CellParam = np.loadtxt(fname=CellParam,dtype=float, encoding=None)
	CellParamMat = ParamHandler(CellParam, paramType)
	if k_Check == 1 : #Only create KPath list if detected in QE input
		KPath = np.genfromtxt(fname=KPath, dtype=None, encoding=None)
		KPathMat = KPathHandler(KPath,"kType")
		ControlConstructor(baseName,k_Check, KPathMat) #Create control file with KPath
	else :
		ControlConstructor(baseName,k_Check) #Create control file without KPath
	#Create FHI-Aims geometry input file
	GeomConstructor(baseName,CellParamMat, GeomMatIn)

	#Debug Option for printing Coordinates, KPath, and Cell Parameters
	debug_Print = 0
	if debug_Print == 1 :
		for i in range(len(CellParamMat)) :
			print( '{0:^16}{1:^16.8f}{2:^16.8f}{3:^16.8f}'.format(CellParamMat[i].inputType,CellParamMat[i].x,
            CellParamMat[i].y,CellParamMat[i].z) )
		for i in range(len(GeomMatIn)) :
			print( '{0:^6}{1:^16.8f}{2:^16.8f}{3:^16.8f}{4:<6}'.format(GeomMatIn[i].inputType,GeomMatIn[i].x,
            GeomMatIn[i].y,GeomMatIn[i].z,GeomMatIn[i].atomType) )
		for i in range(len(KPathMat)) :
			print( '{0:12}{1:13.5f}{2:13.5f}{3:13.5f}{4:13.5f}{5:13.5f}{6:13.5f}{7:4}'.format(KPathMat[i].inputType,KPathMat[i].xi,
	                 KPathMat[i].yi,KPathMat[i].zi,KPathMat[i].xf,KPathMat[i].yf,KPathMat[i].zf,KPathMat[i].step) )
#=======================================#	
class GeomClass : #Class to store atom geometry coordinates and type 
	def __init__ (self, inputType, x, y, z, atomType) :
		self.inputType =  inputType	#Variable for the type of coord- Ang or Fractional
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)
		#self.atomType = str(atomType)
		self.atomType = atomType
class CellParamClass :
	def __init__ (self, inputType, x, y, z) :
		self.inputType = inputType # What is this variable for?
		self.x = float(x)
		self.y = float(y)
		self.z = float(z)
class KPathClass :
	def __init__ (self, inputType, xi, yi, zi, xf, yf, zf, step) :
		self.inputType = inputType #Variable for "output band"
		self.xi = float(xi)
		self.yi = float(yi)
		self.zi = float(zi)
		self.xf = float(xf)
		self.yf = float(yf)
		self.zf = float(zf)
		self.step = step
#=======================================#	
def  KPathHandler(listIn, inputType) : # Function to create K_Path in FHI-Aims format
	#inputType stores the KPath Type, currently assume crystal_b; not used
	TempMat = []
	i = 0
	for i in range(len(listIn) - 1) :
		TempMat.append(KPathClass("output band", listIn[i][0], listIn[i][1], listIn[i][2], 
			         listIn[i+1][0], listIn[i+1][1], listIn[i+1][2],listIn[i][3]))
	return(TempMat)
#=======================================#	
def ParamHandler(listIn, listType) : # Function to convert QE Cell Parameters to FHI-Aims format
	TempMat = []
	for i in range( len(listIn) ) :
	#	TempMat.append(CellParamClass("lattice_vector",listIn[i].split()[0],listIn[i].split()[1],listIn()[i].split[2])) 
		TempMat.append(CellParamClass("lattice_vector", listIn[i][0], listIn[i][1], listIn[i][2]))
	return(TempMat)
#=======================================#	
def GeomHandler(listIn, listType) : # Function to convert QE geometry to FHI-Aims format
	#listType will eventually be used to convert other geometry types (crystal, etc.) to cartesian
	TempMat = []
	for i in range( len(listIn) ) :
		#If loop checks the atom label is numbered e.g. H1 and splits this number off with a ' #'
		if match := re.search('([a-zA-Z]+)([0-9]+)',listIn[i][0]) :  
			label = match.group(1) + " #" + str(match.group(2))
		else :
			label = listIn[i][0]
		TempMat.append(GeomClass("atom",listIn[i][1],listIn[i][2],listIn[i][3],label)) 
	return(TempMat)
#=======================================#	
def FileHandler(fileName) : # Function to read QE input file and return K Path, Geometry,
	k_Check,cell_Check,geom_Check = 0,0,0 # Variables for checking if present in input
	with open(os.path.join(os.getcwd(),fileName), "r") as file :
		fileList = KPath = []
		for line in file :
			if "," in line : #Splits CSV format into seperate lines - Look into using regex here to only split if value after
				fileList.extend(line.split(","))
			else :
				fileList.append(line)
		if fileList[-1] != "\n" :
			fileList.append("\n")
	i = 0
	while i <= (len(fileList[:]) - 1) :
		fileList[i]=fileList[i].strip()
		if "ibrav" in fileList[i] : # Determine ibrav - not utilized currently
			ibravType = fileList[i].split("=")[1]
		elif "K_POINTS" in fileList[i] : #Loop for K Path
			kType = fileList[i].split()[1] #Variable for K Path Type
			i, KPath = BlockCheck(i,fileList,2)
			k_Check = 1
		elif "ATOMIC_POSITIONS" in fileList[i] : #Loop for Atomic Positions
			geomType = fileList[i].split()[1] #Variable for Coords Type
			i, Geom = BlockCheck(i,fileList,1)
		elif "CELL_PARAMETERS" in fileList[i] : #Loop for Cell Parameters
			paramType = fileList[i].split()[1] #Variable for Cell Parameter Type
			i, CellParam = BlockCheck(i,fileList,1)
		i +=1
	return(ibravType, paramType, geomType, Geom, KPath, k_Check, CellParam)
#=======================================#	
def BlockCheck(i,data,skip) : # Function for grabbing data blocks- ends block on new lines
	blockList = []
	i += skip
	while True :
		if data[i] == "\n" or i == (len(data[:]) - 1) :
			break
		else :
			blockList.append(data[i].strip())
			i += 1
	return i, blockList
#=======================================#	
def GeomConstructor(baseName,CellParamMat, GeomMatIn) :
	with open(os.path.join(os.getcwd(), baseName+'.geom'), 'w') as geomin :
		geomin.write("# Cell Parameters Cartesian \n")
		for i in range(len(CellParamMat)) :
			geomin.write( '{0:^16}{1:^16.8f}{2:^16.8f}{3:^16.8f}'.format(CellParamMat[i].inputType,CellParamMat[i].x, 
	                 CellParamMat[i].y,CellParamMat[i].z) + "\n" )
		geomin.write("# Cartesian Geometry \n")
		for i in range(len(GeomMatIn)) :
			geomin.write( '{0:^6}{1:^16.8f}{2:^16.8f}{3:^16.8f}{4:<6}'.format(GeomMatIn[i].inputType,GeomMatIn[i].x,
          GeomMatIn[i].y,GeomMatIn[i].z,GeomMatIn[i].atomType) + "\n" )
#=======================================#	
def ControlConstructor(baseName,k_Check, KPathMat=0) :
	with open(os.path.join(os.getcwd(), baseName+'.ctrl'), 'w') as control :
		with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'control_template'), 'r') as template :
			for line in template :
				control.write(line)
				if "Output band structure (if included)" in line :
					if k_Check == 1 : #Only print KPath if detected in QE Input, also print a missing notice
						control.write("exx_band_structure_version 1 \n")
						for i in range(len(KPathMat)) :
							control.write( '{0:12}{1:13.5f}{2:13.5f}{3:13.5f}{4:13.5f}{5:13.5f}{6:13.5f}{7:4}'.format(KPathMat[i].inputType,KPathMat[i].xi,
	                         KPathMat[i].yi,KPathMat[i].zi,KPathMat[i].xf,KPathMat[i].yf,KPathMat[i].zf,KPathMat[i].step) + "\n" )
					else : 
						control.write("#No K_Path Detected in QE Input File")
#=======================================#	
def FileChecker() :
	try : 
		if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)),'control_template')) is False :
			raise FileNotFoundError
	except FileNotFoundError :
		exit("The control_template file could not be located at: \n" + os.path.join(os.path.dirname(os.path.realpath(__file__)),'control_template') 
       		+ "\nPlease place this file in the same directory as this script")
######################
	try : 
		fileName = sys.argv[1]
	except IndexError :
		exit("No file was given. To use this command specify one QE input file")
	else :
		fileName = sys.argv[1]
		baseName = fileName.split('.')[0]
######################
	try :
		if os.path.exists(os.path.join(os.getcwd(), fileName)) is False :
			raise FileNotFoundError
	except FileNotFoundError :
		exit("The input file was not found in the current directory.")
	return(fileName,baseName)
#=======================================#	
#if __name__ == "__main__" :
#	main()

main()
		
