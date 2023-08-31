#!/bin/bash
#SBATCH -J 1fs-2h-4all
#SBATCH -A m432
#SBATCH --qos regular
#SBATCH --constraint gpu
#SBATCH --output=%j.slurm
#SBATCH --time 12:00:00
#SBATCH --nodes 1
#SBATCH --ntasks-per-node 4
#SBATCH --cpus-per-task 32
#SBATCH --gpus-per-task 1

FNAME=pd192-28h-139w-6hcl-0e
ulimit -s unlimited
module load cray-fftw/3.3.10.3
export OMP_PROC_BIND=true
export OMP_PLACES=threads
export OMP_NUM_THREADS=16
export SLURM_CPU_BIND=cores
CP2K20221=/global/homes/c/cjmundy/SOURCEFORGE_CP2K/cp2kv2022.1/exe/perlmutter-gpu/cp2k.psmp

WFN2=$(ls *wfn.bak-2 2>/dev/null); WFN=$(echo ${WFN2} | sed 's/\.bak-2//')
RSART1=$(ls *-1.restart.bak-1 2>/dev/null); RSTART=$(echo ${RSTART1} | sed 's/\.bak-1//')
if [[ -f ${WFN2} && -f ${WFN} ]]; then
	WFNSIZE2=$(ls -l ${WFN2} | awk '{print $5}')
	WFNSIZE=$(ls -l ${WFN} | awk '{print $5}')
	RSIZE1=$(ls -l ${RSTART1} | awk '{print $5}')
  RSIZE=$(ls -l ${RSTART} | awk '{print $5}')
	if [ ${FSIZE} -lt ${FSIZE2} ] ; then cp ${WFN2} ${WFN} ; fi 
	if [ ${RSIZE} -lt ${RSIZE1} ] ; then cp ${RSTART1} ${RSTART} ; fi 
fi

srun --cpu-bind cores ${CP2K20221} -i ${FNAME}.inp -o ${FNAME}.out


