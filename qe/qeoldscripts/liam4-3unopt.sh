#!/bin/bash -l
#SBATCH --job-name=liam4-3unopt.qe
#SBATCH --nodes=1
#SBATCH --ntasks=20
#SBATCH --cpus-per-task=1
#SBATCH --mem=360GB
#SBATCH --error=liam4-3unopt.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=bigmem2
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
NPROC=20
CURDIR=$(pwd)
FNAME=liam4-3unopt
cd ${CURDIR}
module load espresso/intel/6.8
mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${CURDIR}/${FNAME}.scf.in > ${CURDIR}/${FNAME}.scf.out
mpirun -n ${NPROC} /tools/espresso-6.8/bin/pw.x -inp ${CURDIR}/${FNAME}.nscf.in > ${CURDIR}/${FNAME}.nscf.out
mpirun -n ${NPROC} /tools/espresso-6.8/bin/bands.x -inp ${CURDIR}/${FNAME}.bands.in > ${CURDIR}/${FNAME}.bands.out
if [[ ! -s ${FNAME}.e${SLURM_JOB_ID} ]]; then 
  rm - f ${FNAME}.e${SLURM_JOB_ID}
fi
exit 0
