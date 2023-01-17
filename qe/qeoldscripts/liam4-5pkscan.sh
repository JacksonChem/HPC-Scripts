#!/bin/bash -l
#SBATCH --job-name=liam4-5pkscan.qe
#SBATCH --nodes=1
#SBATCH --ntasks=50
#SBATCH --cpus-per-task=1
#SBATCH --mem=240GB
#SBATCH --error=liam4-5pkscan.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=amd
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
NPROC=50
CURDIR=$(pwd)
FNAME=liam4-5pkscan
cd ${CURDIR}
module load espresso/intel/6.8
i=1
while [[ $i -lt 25 ]]; do
	sed -i 118c"$i $i $i 0 0 0" ${CURDIR}/${FNAME}.in
	mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${CURDIR}/${FNAME}.in >> ${CURDIR}/${FNAME}.out
	((i++))
done
if [[ ! -s ${FNAME}.e${SLURM_JOB_ID} ]]; then 
  rm - f ${FNAME}.e${SLURM_JOB_ID}
fi
exit 0
