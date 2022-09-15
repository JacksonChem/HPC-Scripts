#!/bin/bash -l

#******************************************************#
#                                                      #
#    Script for running VC-Relax in Quantum Espresso   #
#     Intended to work with the SLURM queue system     #
#           within the Easley HPC system               #
#                                                      #
#        Benjamin Jackson, Auburn University           #
#                 baj0040@auburn.edu                   #
#                                                      #
#                Updated: 12/08/2021                   #
#                                                      #
#******************************************************#

Main(){
	FNAME=$(echo ${!#} | awk -F. '{print $1}')

	##Defaults:
	NPROC=48
	MEM=100
	QTYPE=b2
	TIME=200:00:00	
  ##Default paths:
	SUBDIR=/home/$(whoami)/.subfiles
#	SUBDIR=$(pwd)
	CURDIR=$(pwd)
	SCRDIR=/scratch/$(whoami)/pdft/${FNAME}

	#Begin Program
	if [[ "$#" -lt 1 ]]; then Helpfn; exit; fi
	Option_Handler "$@";
	Req_Check;
  QUEUE=$(Queue_Set) 
	Batch_Gen;
	sbatch ${SUBDIR}/${FNAME}.batch
#	rm -f ${SUBDIR}/${FNAME}.batch
}
Option_Handler(){
	while getopts ":hn:m:t:q:" option; do
		case $option in
			h) Helpfn; exit;; #Called help function and exit
			n) NPROC=$OPTARG;;
			N) NODES=$OPTARG;;
			m) MEM=$( echo $OPTARG | sed 's/GB//' );;
			t) TIME=$OPTARG;; #HOUR:MINUTES
			q) QTYPE=$OPTARG;;
		esac
	done
}
Batch_Gen(){
SPOT=EOF
cat > ${SUBDIR}/${FNAME}.batch << EOF
#!/bin/bash -l
#SBATCH --job-name=${FNAME}.qe
${NODE_STR}
${NPROC_STR}
${MEM_STR}
#SBATCH --cpus-per-task=1
#SBATCH --error=${SUBDIR}/${FNAME}.e%j
#SBATCH --time=${TIME}
#SBATCH --output=/dev/null
#SBATCH --partition=${QUEUE}
#SBATCH --mail-user=$(whoami)@auburn.edu
#SBATCH --mail-type=NONE
CURDIR=\$(pwd)
FNAME=${FNAME}
SCRDIR=${SCRDIR}
SUBDIR=${SUBDIR}
if  [[ ! -d \${SCRDIR} ]]; then       #Check if SUBDIR exists, create if not
        mkdir -p \${SCRDIR}
fi
NPROC=${NPROC}
module load espresso/intel/6.8
sed -i s#calculation=.*#calculation=\'vc-relax\',# \${CURDIR}/\${FNAME}.scf.in
sed -i s#prefix=.*#prefix=\'\${FNAME}\',# \${CURDIR}/\${FNAME}.scf.in
sed -i s#outdir=.*#outdir=\'\${SCRDIR}\',# \${CURDIR}/\${FNAME}.scf.in

cp \${CURDIR}/\${FNAME}.scf.in \${SCRDIR}/\${FNAME}.scf.in
mpirun -n \${NPROC} /tools/espresso-6.8/bin/pw.x -inp \${SCRDIR}/\${FNAME}.scf.in > \${CURDIR}/\${FNAME}.scf.out
while true; do
	if [[ -n \$(grep 'The maximum number of steps has been reached' \${CURDIR}/\${FNAME}.scf.out) ]]; then
		cat \${CURDIR}/\${FNAME}.scf.out >> \${CURDIR}/\${FNAME}.scf.out_past
		TEMP_txt=.tempgeom.txt
		TEMP_txt2=.tempgeom2.txt
		PARAM_START=\$(( \$(grep -n 'CELL_PARAMETERS (angstrom)' \${CURDIR}/\${FNAME}.scf.out | tail -1 | awk -F: '{print \$1}') + 1 ))
		PARAM_END=\$(( \${PARAM_START} + 2))
		sed -n \${PARAM_START},\${PARAM_END}p \${CURDIR}/\${FNAME}.scf.out > \${SCRDIR}/\${TEMP_txt2}
		START_OUT=\$(( \$(grep -n 'ATOMIC_POSITIONS (angstrom)' \${CURDIR}/\${FNAME}.scf.out | tail -1 | awk -F: '{print \$1}')	+ 1 ))
		END_OUT=\$(( \$(grep -n 'Writing output data' \${CURDIR}/\${FNAME}.scf.out | tail -1 | awk -F: '{print \$1}') - 6 ))
		sed -n \${START_OUT},\${END_OUT}p \${CURDIR}/\${FNAME}.scf.out > \${SCRDIR}/\${TEMP_txt}
		sed -i '/^$/d' \${SCRDIR}/\${TEMP_txt}
		START_IN=\$(( \$(grep -n 'ATOMIC_POSITIONS angstrom' \${SCRDIR}/\${FNAME}.scf.in | awk -F: '{print \$1}') + 1 ))
		END_IN=\$(( \$(grep -n 'K_POINTS' \${SCRDIR}/\${FNAME}.scf.in | awk -F: '{print \$1}') - 2 ))
		sed -i \${START_IN},\${END_IN}d \${SCRDIR}/\${FNAME}.scf.in 
		sed -i "/ATOMIC_POSITIONS angstrom/r \${SCRDIR}/\${TEMP_txt}" \${SCRDIR}/\${FNAME}.scf.in	
		PARAM_IN=\$( grep -n 'CELL_PARAMETERS angstrom' \${SCRDIR}/\${FNAME}.scf.in | awk -F: '{print \$1}')  
		sed -i \$(( \${PARAM_IN} + 1 )),\$(( \${PARAM_IN} + 3 ))d \${SCRDIR}/\${FNAME}.scf.in
		sed -i "/CELL_PARAMETERS angstrom/r \${SCRDIR}/\${TEMP_txt2}" \${SCRDIR}/\${FNAME}.scf.in
		rm -f \${SCRDIR}/\${TEMP_txt} \${SCRDIR}/\${TEMP_txt2}
		mpirun -n \${NPROC} /tools/espresso-6.8/bin/pw.x -inp \${SCRDIR}/\${FNAME}.scf.in > \${CURDIR}/\${FNAME}.scf.out
	else
		break
	fi
done
if [[ ! -s \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ]]; then
  rm -f \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID}
else
  mv \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} \${CURDIR}/.
fi
exit 0
EOF
}
Queue_Set(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
  if [[ "$QTYPE" = "b2" ]]; then echo "bigmem2";
  	elif [[ "$QTYPE" = "rb2" ]]; then echo "ezm0048_bg2"; 
  	elif [[ "$QTYPE" = "b4" ]]; then echo "bigmem4";
  	elif [[ "$QTYPE" = "a" ]]; then echo "amd";
  	elif [[ "$QTYPE" = "gpu" ]]; then echo "gpu2";
  	elif [[ "$QTYPE" = "r" ]]; then echo "ezm0048_std";
  	else echo "general";
  fi
}
Req_Check(){
 case $QTYPE in
	rb2 | b2 ) NMAX=48; MEMMAX=384;;
	b4) NMAX=48; MEMMAX=768;;
	a | amd) NMAX=128; MEMMAX=256;;
	gpu2 | gpu4) echo "This script is not setup for GPU calculations- please resubmit with another queue"; exit 30 ;;
	s | * ) NMAX=48; MEMMAX=192;;
 esac
	if [[ ${NPROC} -gt ${NMAX} ]]; then NODES_NPROC= $(( ${NMAX} / ${NPROC} )); fi
	if [[ ${MEM} -gt ${MEMMAX} ]]; then NODES_MEM= $(( ${MEM} / ${MEMMAX} )); fi

	if [[ ${NODES_NPROC} -gt ${NODES_MEM} ]]; then NODES=${NODES_NPROC};
		elif [[ ${NODES_MEM} -gt ${NODES_NPROC} ]]; then NODES=${NODES_MEM};
		else NODES=1; fi
	if [[ ${NODES} -eq 1 ]]; then MEM_STR="#SBATCH --mem=${MEM}GB";
		else MEM_STR="#SBATCH --mem-per-cpu=$(( ${MEM} / ${NPROC} ))"; 
	fi	
	NPROC_STR="#SBATCH --ntasks=${NPROC}"	
	NODE_STR="#SBATCH --nodes=${NODES}"
	if [[ ${NODE_LIMIT} -eq 1 ]]; then
		if [[ ${MEM} -gt ${MEMMAX} ]]; then
			echo "You have request more memory than is available for this queue; this process is unable to run on multiple nodes"
			exit 10
		fi
		if [[ $NPROC -gt $NMAX ]]; then
			echo "You have more processors than is available on a node; this process is unable to run on multiple nodes"
			exit 15
		fi
	fi
}
Old_Req_Check(){ #Deprecated
	if [[ "$QTYPE" = "rb2" || "$QTYPE" = "b2" || "$QTYPE" = "b4" || "$QTYPE" = "gpu" ]]; then NMAX=48;
		if [[ "$QTYPE" = "b2" || "$QTYPE" = "rb2" ]]; then MEMMAX=384; fi
		if [[ "$QTYPE" = "b4" ]]; then MEMMAX=768; fi
		if [[ "$QTYPE" = "gpu" ]]; then
			echo "This script is not setup for GPU calculations- please resubmit with another queue"
			exit 30
		fi
		elif [[ "$QTYPE" = "a" ]]; then NMAX=128; MEMMAX=256;
		else NMAX=48; MEMMAX=192;
	fi
}
Helpfn(){
echo "
You have run the vcrelax script for Quantum Espresso calculations. This script will automatically create a batch job for you. 
It is set up to automatically check for convergence and if not achieved to restart with the last geometry. All runs will be saved in one file.
The output files will automatically be placed in the current directory.
Input files must be of the form: file.scf.in
Output files will be of the form: file.scf.out

      Options:
       -h    |   Help, display this current usage guide
       -n    |   Number of Processors Requested
       -m    |   Memory Requested in GB; Specifying the GB units is optional
       -t    |   Time Limit for Jobs in HR:MIN format
       -N    |   Number of nodes to run on; this is unnecessary as the nodes will be determined by your resources request
       -q    |   Which queue this job will be submitted to; Options: b2- bigmem2, rb2- Investor bigmem2, b4-bigmem4, a-amd,
             |      gpu-GPU2, r-Investor general, s- general nodes       

You may specify these in any order, but the filename must be the last value specified. 

If -n, -m, -t, -N, and -q are not specified default values will be used.

Your current defaults are:
       Proc   =   ${NPROC}
       Memory =   ${MEM}
       Time   =   ${TIME}
       Queue  =   ${QUEUE}
You can change this in $(echo $0)

EXAMPLE:
$(echo $0) -n 12 -m 24GB -t 10:00 -q b2 file.scf.in
"
}
Main "$@"; exit
