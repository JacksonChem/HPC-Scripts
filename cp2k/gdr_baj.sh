#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=28
#SBATCH -t 2-00:00:00
#SBATCH --partition=nova

prefix=$1
#prefix="liam5o1_nn2_md150s5"
posFile=${prefix}-pos-1.xyz
cellFile=${prefix}-1.cell
numStepsRead=`grep E $prefix-pos-1.xyz | wc -l`
numStepsAnalList=$2
gausBroadenList="0.02"
EXE="/home/baj0040/bin/mlee/gdr.lee.zeolite.mol.new.x" 

numSpecs=4
numCorrelation=4

for gaus in ${gausBroadenList}; do
	echo $gaus
	for numAnal in ${numStepsAnalList}; do
	  stepStart=$(( ${numStepsRead} - ${numAnal} + 1 ))
		echo $nit  $n_left
		cat >  gdr.in  <<- EOF
			${posFile} ${cellFile} gdr.${numAnal}.dat g_gdr.${gaus}.${numAnal}.dat
			${numSpecs}  ${numCorrelation}  ! no. of species, no. of g of r
			16 64 160 448       ! no. of at per sp
			1  1  1   1         ! number of different atom types in each group
			Li N  C   H         ! name of species
			1 1 !Li-Li
			1 2 !Li-N
			1 3 !Li-C
			2 4 !N-H
			${numStepsRead} ${stepStart} 1 1 #total number, which structure to start from, skip? skip?
			${gaus}
		EOF
		${EXE} < gdr.in 
	done
done
