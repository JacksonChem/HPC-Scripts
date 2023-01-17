#!/bin/bash -l
#SBATCH --job-name=liam4-5prhoscan.qe
#SBATCH --nodes=1
#SBATCH --ntasks=48
#SBATCH --cpus-per-task=1
#SBATCH --mem=240GB
#SBATCH --error=liam4-5prhoscan.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=bigmem2
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
NPROC=48
CURDIR=$(pwd)
FNAME=liam4-5prhoscan
module load espresso/intel/6.8
ecutwf=35
ecutrho=350
i=0
while [[ $i -lt 50 ]]; do
        findwfc=$(grep 'ecutwfc' ${FNAME}.in)
        findrho=$(grep 'ecutrho' ${FNAME}.in)
        sed -i s/"$findwfc"/' ecutwfc='"$ecutwf",/ ${FNAME}.in
        sed -i s/"$findrho"/' ecutrho='"$ecutrho",/ ${FNAME}.in
	mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${CURDIR}/${FNAME}.in >> ${CURDIR}/${FNAME}.out
        ((ecutwf=ecutwf+3))
        ((ecutrho=10*ecutwf))
        findwfc=$(grep 'ecutwfc' ${FNAME}.in)
        findrho=$(grep 'ecutrho' ${FNAME}.in)
        sed -i s/"$findwfc"/' ecutwfc='"$ecutwf",/ ${FNAME}.in
        sed -i s/"$findrho"/' ecutrho='"$ecutrho",/ ${FNAME}.in
        ((i++))
done
exit 0
if [[ ! -s ${FNAME}.e${SLURM_JOB_ID} ]]; then 
  rm - f ${FNAME}.e${SLURM_JOB_ID}
fi
exit 0
