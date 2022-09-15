#!/tools/anacondapython-3.8.6/bin/python


import math
import numpy
import sys
import subprocess as sub
#Create Intensity List
outFile=sys.argv[5]
startFreq = float(sys.argv[1])
endFreq = float(sys.argv[2])
stepCount = int(sys.argv[3])
widthSize = float(sys.argv[4])

def gen_List(fileName, scriptName) :
	out=sub.check_output([scriptName, fileName])
	out=(out.decode('utf-8').splitlines())
	tempList=[]
	for element in out :
		tempList.append(float(element))
	return(tempList)
	
freqList=gen_List(outFile, "freq")
intenList=gen_List(outFile, "ir")
dx = (endFreq-startFreq)/float(stepCount)
irMat = numpy.zeros((stepCount+1,2), dtype=float)
for k in range(0,stepCount+1) :
	x_Val = startFreq+k*dx
	irMat[k,0] = x_Val
	for i in range(1,len(freqList)):
		irMat[k,1] = irMat[k,1] + intenList[i]*math.exp(-2.7725887*( ((x_Val-freqList[i])/widthSize )**2.0) )
maxInt=max(irMat[:,1])
for i in range(0,len(irMat[:,0])) :
	irMat[i,1] = irMat[i,1]/maxInt
	if irMat[i,1] < 1e-30 :
		irMat[i,1] = 0
#for line in irMat :
#	print ('  '.join(map(str, line)))
for line in irMat[:,1] :
	print (line)

#Create Frequencies List
#out=sub.check_output(['freq', outFile])
#out=(out.decode('utf-8').splitlines())
#freqList=[]
#for element in out :
#	freqList.append(float(element))

