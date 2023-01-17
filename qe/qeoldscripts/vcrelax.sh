#!/bin/bash -l

FNAME=$(echo $1 | awk -F. '{print $1}')
SUBDIR=/home/$(whoami)/.subfiles
CURDIR=$(pwd)
SCRDIR=/scratch/$(whoami)/pdft/${FNAME}
SPOT=EOF
cat > ${SUBDIR}/${FNAME}.batch << EOF
#!/bin/bash -l
#SBATCH --job-name=${FNAME}.qe
#SBATCH --nodes=1
#SBATCH --ntasks=25
#SBATCH --cpus-per-task=1
#SBATCH --mem=100GB
#SBATCH --error=${SUBDIR}/${FNAME}.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=general
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
CURDIR=$(pwd)
FNAME=${FNAME}
SCRDIR=/scratch/$(whoami)/pdft/${FNAME}
SUBDIR=/home/$(whoami)/.subfiles
if  [[ ! -d ${SCRDIR} ]]; then       #Check if SUBDIR exists, create if not
        mkdir -p ${SCRDIR}
fi
NPROC=25
module load espresso/intel/6.8
sed -i s#prefix=.*#prefix=\'\${FNAME}\',# \${FNAME}.scf.in
sed -i s#outdir=.*#outdir=\'\${SCRDIR}\',# \${FNAME}.scf.in

cp \${CURDIR}/\${FNAME}.scf.in \${SCRDIR}/\${FNAME}.scf.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/pw.x -inp \${SCRDIR}/\${FNAME}.scf.in >> \${CURDIR}/\${FNAME}.scf.out

if [[ ! -s \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ]]; then
  rm -f ${SUBDIR}/${FNAME}.e\${SLURM_JOB_ID}
else
  mv \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ${CURDIR}/.
fi
exit 0
EOF
sbatch ${SUBDIR}/${FNAME}.batch
rm -f ${SUBDIR}/${FNAME}.batch

