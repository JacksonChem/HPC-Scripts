#!/bin/bash -l

#******************************************************#
#                                                      #
#         Script for running Quantum Espresso          #
#     Intended to work with the SLURM queue system     #
#           within the Easley HPC system               #
#                                                      #
#        Benjamin Jackson, Auburn University           #
#                 baj0040@auburn.edu                   #
#                                                      #
#                Updated: 08/18/2022                   #
#                                                      #
#******************************************************#

Main(){
	FNAME=$(echo ${!#} | awk -F. '{print $1}')
  ##Defaults:
	NPROC=12
	QTYPE=g
	TIME=200:00	
	NODE_LIMIT=1 #Set value to 1 if process cannot run as multinode
	FILE_EDIT=1  #Setting to autorename .wfc and .int in your input file, 1 for on
	SAVE_INT=1   #Setting to save .int file, 1 for on
	SCR_CLEAN=1 #Setting to autoclean molpro job folders in scratch
	THREADS=1
  ##Default paths:
	SUBDIR=/scratch/$(whoami)/.subfiles
	WRKDIR=$(pwd)
	SCRDIR=/scratch/$(whoami)/${FNAME}
	BACKUPDIR=/home/$(whoami)/trash/overwrite
	SCRIPT_PATH=$( dirname "$(readlink -f "$0")" )
	##Modules
	MOLPRO_MODULE=molpro/2021.3 
	#GCC_MODULE=gcc/4.8.5 
	GCC_MODULE=gcc/9.3.0 
	MPI_MODULE=openmpi/4.0.3
	#GA_MODULE=ga/5.8.1 
	#Begin Program
	if [[ ! -d ${SCRDIR} ]]; then mkdir -p ${SCRDIR}; fi
	if [[ ! -d ${SUBDIR} ]]; then mkdir -p ${SUBDIR}; fi
	if [[ ! -d ${BACKUPDIR} ]]; then mkdir -p ${BACKUPDIR}; fi
	if [[ "$#" -lt 1 ]]; then Helpfn; exit; fi
	Option_Handler "$@";
	if [[ ! -e ${FNAME}.com ]]; then echo "Input file was not found"; exit 30; fi
	if [[ ${FILE_EDIT} = 1 ]]; then 
		sed -i "s#file,1,[[:graph:]]*.int,#file,1,${FNAME}.int,#" ${FNAME}.com
		sed -i "s#file,2,[[:graph:]]*.wfc,#file,2,${FNAME}.wfc,#" ${FNAME}.com 
	fi
	Mem_Handler;
	Req_Check;
  QUEUE=$(Queue_Set)
	Maint_Check;
	Batch_Builder;
	if [[ ${STOP} = 1 ]]; then mv ${SUBDIR}/${FNAME}.batch ${WRKDIR}/; exit; fi
	sbatch ${SUBDIR}/${FNAME}.batch
	rm -f ${SUBDIR}/${FNAME}.batch
}
Option_Handler(){
	while getopts ":hN:n:m:t:q:go:" option; do
		case $option in
			h) Helpfn; exit;;  #Call help function and exit
			n) NPROC=$OPTARG;; #Number of Processors
			N) NODES=$OPTARG;; #Number of Nodes
			m) MEM=$( echo $OPTARG | sed 's/GB//' );; #Memory Request
			t) TIME=$OPTARG;;  #HOUR:MINUTES
			q) QTYPE=$OPTARG;; #Type of Queue
			g) STOP=1;;        #Create batch file then exit
			o) Old_Handler "$@"; break;; #Legacy job submission
		esac
	done
}
Batch_Builder(){
	Opening_Gen;
	Molpro_Gen;
	Closer_Gen;	
}
Opening_Gen(){
	cat > ${SUBDIR}/${FNAME}.batch <<- EOF
		#!/bin/bash -l
		#SBATCH --job-name=${FNAME}.m21
		${NODE_STR}
		${NTASKS_STR}
		${THRD_STR}
		${MEM_STR}
		#SBATCH --error=${SUBDIR}/${FNAME}.err%j
		#SBATCH --time=${TIME}:00
		#SBATCH --output=/dev/null
		#SBATCH --partition=${QUEUE}
		#SBATCH --mail-user=$(whoami)@auburn.edu
		#SBATCH --mail-type=NONE
		###SBATCH --no-requeue
		WRKDIR=\$(pwd)
		FNAME=${FNAME}
		SCRDIR=${SCRDIR}
		SUBDIR=${SUBDIR}
	EOF
}
Molpro_Gen(){
	if [[ ${SAVE_INT} = 1 ]]; then INT_STR="-I \${SCRDIR}"; fi
	if [[ ${SCR_CLEAN} = 1 ]]; then rm -rf ${SCRDIR}/molpro.*; fi
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		NPROC=${NPROC}
		module load ${MOLPRO_MODULE}
		module load ${GCC_MODULE}
		module load ${GA_MODULE}
		module load ${MPI_MODULE}
		set env OMP_NUM_THREADS=${THREADS}
		cd \${SCRDIR}
		molpro -D \${SCRDIR} -d \${SCRDIR} --no-xml-output -n \${NPROC} -t ${THREADS} ${INT_STR} -W \${SCRDIR} -o \${WRKDIR}/${FNAME}.out \${WRKDIR}/${FNAME}.com
	EOF
}
Closer_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		if [[ ! -s \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID} ]]; then rm -f \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID}
		else mv \${SUBDIR}/\${FNAME}.err\${SLURM_JOB_ID} \${WRKDIR}/.
		fi
		#Check for molden files
		MOLDEN_FILE=\$(grep '^put,molden,' ${FNAME}.com | awk -F, '{print \$3}' | awk -F'!' '{print \$1}' | awk -F'#' '{print \$1}') 
		if [[ -n \${MOLDEN_FILE} && \${SCRDIR}/\${MOLDEN_FILE} ]]; then mv \${SCRDIR}/\${MOLDEN_FILE} \${WRKDIR}/\${MOLDEN_FILE}; fi
		exit 0
	EOF
}
Old_Handler(){
	NPROC=$2
	TIME="$3:$4"
}
Mem_Handler(){
	if [[ -n $(grep -i 'memory' ${FNAME}.com | awk -F, '{print $2}') ]]; then
		MEM_UNIT=$(grep -i 'memory' ${FNAME}.com | awk -F, '{print $3}')
		MEM_IN=$(grep -i 'memory' ${FNAME}.com | awk -F, '{print $2}')
		case ${MEM_UNIT} in
			[kK])MEM_WORDS=$((${MEM_IN}*1000));;
			[mM])MEM_WORDS=$((${MEM_IN}*1000000));;
			[gG])MEM_WORDS=$((${MEM_IN}*1000000000));;
		esac
		#MEM_GIGS=$((${MEM_WORDS}*8/1000/1000/1000))
		NPROC_NoHelper=$(( ${NPROC} - 1))
		MEM=$( Round_Up "${MEM_WORDS}*8/1024/1024/1024*${NPROC_NoHelper}")
	else
		echo "You did not specify a memory request in your input file"
		exit 60
	fi
}
Maint_Check(){
	Queue_Limit=$(/tools/scripts/max_walltime.sh | grep 'Wall-time (hours)' | awk -F: '{print $2}' | sed 's/ //') 
	Time_Req=$( Round_Up $( echo ${TIME} | awk -F: '{print $1  * 60 +  $2 }') )
	if [[ -s Queue_Limit ]] && [[ $(( ${Queue_Limit} * 60 )) -lt ${Time_Req} ]]; then TIME="${Queue_Limit}:00"; fi 
}
Queue_Set(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case ${QTYPE} in
		b2) echo "bigmem2";;
		rb2) echo "ezm0048_bg2";;
		b4) echo "bigmem4";;
		a) echo "amd";;
		gpu2 | g2) echo "gpu2";;
		gpu4 | g4) echo "gpu4";;
		r) echo "ezm0048_std";;
		n) echo "nova";;
		*) echo "general";;
	esac
}
Req_Check(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case $QTYPE in
		rb2 | b2 ) NMAX=48; MEMMAX=384;;
		b4) NMAX=48; MEMMAX=768;;
		a | amd) NMAX=128; MEMMAX=256;;
		gpu2 | g2)NMAX=48; MEMMAX=376;; 
		gpu4 | g4)NMAX=48; MEMMAX=755;;
		n ) NMAX=24; MEMMAX=150;;
		s | * ) NMAX=48; MEMMAX=192;;
	esac
	if [[ ${NPROC} -gt ${NMAX} ]]; then NODES_NPROC=$( Div_Rounder "${NPROC}" "${NMAX}" ); fi
	if [[ ${MEM} -gt ${MEMMAX} ]]; then NODES_MEM=$( Div_Rounder "${MEM}" "${MEMMAX}" ); fi
	if [[ ${NODES_NPROC} -gt ${NODES_MEM} ]]; then NODES=${NODES_NPROC};
		elif [[ ${NODES_MEM} -gt ${NODES_NPROC} ]]; then NODES=${NODES_MEM};
		else NODES=1; fi
	if [[ ${NODES} -eq 1 ]]; then MEM_STR="#SBATCH --mem=${MEM}GB";
		else MEM_STR="#SBATCH --mem-per-cpu=$( Div_Rounder "${MEM}" "$(( ${NPROC} - 1))" )GB"
	fi	
	#Set up a handler for controlling tasks per node here
	#SBATCH --ntasks-per-node=; 
	NTASKS_STR="#SBATCH --ntasks=${NPROC}"	
	NODE_STR="#SBATCH --nodes=${NODES}"
	THRD_STR="#SBATCH --cpus-per-task=${THREADS}"
	if [[ ${NODE_LIMIT} -eq 1 ]]; then
		if [[ ${MEM} -gt ${MEMMAX} ]]; then
			echo "You have requested more memory than is available for this queue; if needed, request additional nodes"
			exit 10
		fi
		if [[ $NPROC -gt $NMAX ]]; then
			echo "You have requested more processors than is available on a node; if needed, request additional nodes"
			exit 15
		fi
	fi
}
Helpfn(){
echo "
You have run the m21 job submission script for Molpro 2021.3. This script will automatically create a batch job for you. 

The output files will automatically be placed in the current directory.
Input files must be of the form:  [file].com
Output files will be of the form: [file].out

      Options:
       -h    |   Help, display this current usage guide
       -o    |   Legacy submission format
       -n    |   Number of Processors Requested
       -m    |   Memory Requested in GB; Specifying the GB units is optional- Unnecessary as molpro memory requests are 
             |      determined from your input file
       -t    |   Time Limit for Jobs in HR:MIN format
       -N    |   Number of nodes to run on; this is unnecessary as the nodes will be determined by your resources request
       -q    |   Which queue this job will be submitted to; Options: b2- bigmem2, rb2- Investor bigmem2, b4-bigmem4, a-amd,
             |      gpu-GPU2, r-Investor general, g- general nodes       

You may specify these in any order, but the filename must be the last value specified. 

If -n, -m, -t, -N, and -q are not specified default values will be used.

Your current defaults are:
       Proc    =   ${NPROC}
       Time    =   ${TIME}
       Queue   =   ${QTYPE}/$(Queue_Set)
You can change this in $(echo $0)

EXAMPLE:
$(echo $0) -n 12 -t 10:00 -q b2 file.com 
"
}
Round_Up(){
echo $( python -c "print( int( -(-${1} // 1) ) )"   )
}
Div_Rounder(){
	A=$1
	B=$2
	if [[ $( python -c "print(${A}%${B})" ) -ne 0 ]]; then
		echo $( python -c "print( int( ((${A}-(${A}%${B}))/${B}+1) ) )" )
		else echo $( python -c "print( int(${A}/${B}) )" )
	fi
}
Main "$@"; exit
