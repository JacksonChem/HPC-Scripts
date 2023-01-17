#!/bin/bash -l
#SBATCH --job-name=liam4-5pvcr.qe
#SBATCH --nodes=1
#SBATCH --ntasks=100
#SBATCH --cpus-per-task=1
#SBATCH --mem=250GB
#SBATCH --error=liam4-5pvcr.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=amd
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
NPROC=100
CURDIR=$(pwd)
FNAME=liam4-5pvcr
cd ${CURDIR}
module load espresso/intel/6.8
mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${CURDIR}/${FNAME}.in >> ${CURDIR}/${FNAME}.out
if [[ ! -s ${FNAME}.e${SLURM_JOB_ID} ]]; then 
  rm - f ${FNAME}.e${SLURM_JOB_ID}
fi
exit 0
