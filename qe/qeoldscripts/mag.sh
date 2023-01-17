#!/bin/bash -l

FNAME=$(echo $1 | awk -F. '{print $1}')
SUBDIR=/home/$(whoami)/.subfiles
CURDIR=$(pwd)
SCRDIR=/scratch/$(whoami)/pdft/${FNAME}
SPOT=$( echo "EOF")
NPROC=25
cat > ${SUBDIR}/${FNAME}.batch << EOF
#!/bin/bash -l
#SBATCH --job-name=${FNAME}.qe
#SBATCH --nodes=1
#SBATCH --ntasks=${NPROC}
#SBATCH --cpus-per-task=1
#SBATCH --mem=350GB
#SBATCH --error=${SUBDIR}/${FNAME}.e%j
#SBATCH --time=200:0:00
#SBATCH --output=/dev/null
#SBATCH --partition=ezm0048_bg2
#SBATCH --mail-user=baj0040@auburn.edu
#SBATCH --mail-type=NONE
CURDIR=$(pwd)
FNAME=${FNAME}
SCRDIR=/scratch/$(whoami)/pdft/\${FNAME}
SUBDIR=/home/$(whoami)/.subfiles
if  [[ ! -d \${SCRDIR} ]]; then       #Check if SUBDIR exists, create if not
        mkdir -p \${SCRDIR}
fi
NPROC=${NPROC}
module load espresso/intel/6.8
sed -i s#prefix=.*#prefix=\'\${FNAME}\',# \${FNAME}.scf.in
sed -i s#prefix=.*#prefix=\'\${FNAME}\',# \${FNAME}.nscf.in
sed -i s#outdir=.*#outdir=\'\${SCRDIR}\',# \${FNAME}.scf.in
sed -i s#outdir=.*#outdir=\'\${SCRDIR}\',# \${FNAME}.nscf.in

cp \${CURDIR}/\${FNAME}.scf.in \${SCRDIR}/\${FNAME}.scf.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/pw.x -inp \${SCRDIR}/\${FNAME}.scf.in > \${CURDIR}/\${FNAME}.scf.out
cp \${CURDIR}/\${FNAME}.nscf.in \${SCRDIR}/\${FNAME}.nscf.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/pw.x -inp \${SCRDIR}/\${FNAME}.nscf.in > \${CURDIR}/\${FNAME}.nscf.out

#cat > \${FNAME}.bands.in << ${SPOT}
#&bands
# prefix='\${FNAME}',
# outdir = '\${SCRDIR}'
# filband='\${FNAME}.dat',
#/
#${SPOT}
#cp \${CURDIR}/\${FNAME}.bands.in \${CURDIR}/\${FNAME}.bands.out
#mv \${CURDIR}/\${FNAME}.bands.in \${SCRDIR}/\${FNAME}.bands.in
#mpirun -n \${NPROC} /tools/espresso-6.8/bin/bands.x -inp \${SCRDIR}/\${FNAME}.bands.in >> \${CURDIR}/\${FNAME}.bands.out
cat > \${FNAME}.bands2.in << ${SPOT}
&bands
 prefix='\${FNAME}',
 outdir='\${SCRDIR}',
 filband='\${FNAME}.spin2.dat',
 spin_component=2
/
${SPOT}
cat > \${FNAME}.bands1.in << ${SPOT}
&bands
 prefix='\${FNAME}',
 outdir='\${SCRDIR}',
 filband='\${FNAME}.spin1.dat',
 spin_component=1,
/
${SPOT}

cp \${CURDIR}/\${FNAME}.bands1.in \${CURDIR}/\${FNAME}.bands1.out
mv \${CURDIR}/\${FNAME}.bands1.in \${SCRDIR}/\${FNAME}.bands1.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/bands.x -inp \${SCRDIR}/\${FNAME}.bands1.in >> \${CURDIR}/\${FNAME}.bands1.out
cp \${CURDIR}/\${FNAME}.bands2.in \${CURDIR}/\${FNAME}.bands2.out
mv \${CURDIR}/\${FNAME}.bands2.in \${SCRDIR}/\${FNAME}.bands2.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/bands.x -inp ${SCRDIR}/${FNAME}.bands2.in >> ${CURDIR}/${FNAME}.bands2.out

NX=\$(grep 'Den' ${FNAME}.scf.out | awk -F'(' '{print \$2}' | awk -F')' '{print \$1}' | awk -F',' '{print \$1}')
NY=\$(grep 'Den' ${FNAME}.scf.out | awk -F'(' '{print \$2}' | awk -F')' '{print \$1}' | awk -F',' '{print \$2}')
NZ=\$(grep 'Den' ${FNAME}.scf.out | awk -F'(' '{print \$2}' | awk -F')' '{print \$1}' | awk -F',' '{print \$3}')
#Make Spinden file
cat > \${FNAME}.spinden.in << ${SPOT}
&inputpp
 prefix='\${FNAME}',
 outdir='\${SCRDIR}',
 plot_num=6,
/
&plot
 iflag=3,
 output_format=6,
 fileout='\${FNAME}.spin.cube',
 nx=\${NX},ny=\${NY},nz=\${NZ},
/
${SPOT}

#Run Spinden
cp \${CURDIR}/\${FNAME}.spinden.in \${CURDIR}/\${FNAME}.spinden.out
mv \${CURDIR}/\${FNAME}.spinden.in \${SCRDIR}/\${FNAME}.spinden.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/pp.x -inp \${SCRDIR}/\${FNAME}.spinden.in >> \${CURDIR}/\${FNAME}.spinden.out

if [[ ! -s \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ]]; then 
  rm -f \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID}
else
  mv \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} \${CURDIR}/.
fi
rm -f ${SUBDIR}/${FNAME}.batch
exit 0
EOF
sbatch ${SUBDIR}/${FNAME}.batch
