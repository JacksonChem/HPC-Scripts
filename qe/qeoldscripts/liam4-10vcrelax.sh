#!/bin/bash -l
#SBATCH --job-name=liam4-10pvcr.qe
#SBATCH --nodes=1
#SBATCH --ntasks=48
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=7GB
#SBATCH --error=liam4-10pvcr.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=bigmem2
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
NPROC=48
CURDIR=$(pwd)
FNAME=liam4-10pvcr
SCRDIR=/scratch/$(whoami)/pdft/${FNAME}
if  [[ ! -d ${SCRDIR} ]]; then       #Check if SUBDIR exists, create if not
        mkdir -p ${SCRDIR}
fi
cd ${SCRDIR}
module load espresso/intel/6.8
cp ${CURDIR}/${FNAME}.in ${SCRDIR}/${FNAME}.in
mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${SCRDIR}/${FNAME}.in >> ${CURDIR}/${FNAME}.out
if [[ ! -s ${FNAME}.e${SLURM_JOB_ID} ]]; then 
  rm - f ${FNAME}.e${SLURM_JOB_ID}
fi
exit 0
cd ${CURDIR}
