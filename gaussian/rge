#!/bin/bash -l

#******************************************************#
#                                                      #
#           Script for running Gaussian 16             #
#     Intended to work with the SLURM queue system     #
#           within the Easley HPC system               #
#                                                      #
#        Benjamin Jackson, Auburn University           #
#                 baj0040@auburn.edu                   #
#                                                      #
#                Updated: 08/18/2022                   #
#                                                      #
#******************************************************#

##--------------------------------------------------------##
##                   Easley Resources                     ##
## Standard: 48  Cores 192 GB 3.00 GHz Partition: general ##
## Bigmem2 : 48  Cores 384 GB 3.00 GHz Partition: bigmem2 ##
## Bigmem4 : 48  Cores 768 GB 3.00 GHz Partition: bigmem4 ##
## Nova    : 24  Cores 150?GB 3.30 GHz Partition: nova    ##
## AMD     : 128 Cores 256 GB 2.00 GHz Partition: amd     ##
## 2xGPU   : 48  Cores 384 GB 3.00 GHz Partition: gpu2    ##
## 4xGPU+  : 48  Cores 768 GB 3.00 GHz Partition: gpu4    ##
##--------------------------------------------------------##

Main(){
	FNAME=$(echo ${!#} | awk -F. '{print $1}')
  ##Defaults:
	NPROC=12
	QTYPE=g
	TIME=200:00	
	REQUEUE_OPT=0 #Set value to 1 if you want to allow jobs to requeue 
	NODE_LIMIT=1  #Set value to 1 if process cannot run as multinode
	FILE_EDIT=1   #Setting to autorename .wfc and .int in your input file, 1 for on
	#SCR_CLEAN=1  #Setting to autoclean molpro job folders in scratch
	THREADS=1
	NODES=1
  ##Default paths:
	#SUBDIR=$(pwd)
	SUBDIR=/scratch/$(whoami)/.subfiles
	WRKDIR=$(pwd)
	SCRDIR=/scratch/$(whoami)/g16/${FNAME}
	BACKUPDIR=/home/$(whoami)/trash/overwrite
	SCRIPT_PATH=$( dirname "$(readlink -f "$0")" )
	#Begin Program
	if [[ ! -d ${SUBDIR} ]]; then mkdir -p ${SUBDIR}; fi
	if [[ ! -d ${SCRDIR} ]]; then mkdir -p ${SCRDIR}; fi
	if [[ ! -d ${BACKUPDIR} ]]; then mkdir -p ${BACKUPDIR}; fi
	if [[ "$#" -lt 1 ]]; then Helpfn; exit; fi
	Option_Handler "$@";
	if [[ ! -e ${FNAME}.inp ]]; then echo "Input file was not found"; exit 30; fi
	Mem_Handler;
	CPU_Handler;
	Req_Check;
  QUEUE=$(Queue_Set)
	Maint_Check;
	Batch_Builder;
	if [[ ${STOP} = 1 ]]; then mv ${SUBDIR}/${FNAME}.batch ${WRKDIR}/; exit; fi
	sbatch ${SUBDIR}/${FNAME}.batch
	#rm -f ${SUBDIR}/${FNAME}.batch
}
Option_Handler(){
	while getopts ":hN:n:m:t:q:go:" option; do
		case $option in
			h) Helpfn; exit;;  #Call help function and exit
			n) NPROC=$OPTARG; NPROC_CUSTOM=1;; #Number of Processors
			N) NODES=$OPTARG;; #Number of Nodes
			m) MEM_JOB=$( echo $OPTARG | sed 's/GB//' ); MEM_CUSTOM=1;; #Memory Request
			t) TIME=$OPTARG;;  #HOUR:MINUTES
			q) QTYPE=$OPTARG;; #Type of Queue
			g) STOP=1;;        #Create batch file then exit
		esac
	done
}
Batch_Builder(){
	if [[ ${REQUEUE_OPT} -eq 1 ]]; 
		then REQUEUE_STR=""; else REQUEUE_STR="#SBATCH --no-requeue"; fi
	Opening_Gen;
	if [[ ${FILE_EDIT} = 1 ]]; then File_Editor; fi
	G16_Gen;
	Closer_Gen;	
}
Opening_Gen(){
	cat > ${SUBDIR}/${FNAME}.batch <<- EOF
		#!/bin/bash -l
		#SBATCH --job-name=${FNAME}.g16
		${NODE_STR}
		${NTASKS_STR}
		${THRD_STR}
		${MEM_STR}
		#SBATCH --error=${SUBDIR}/${FNAME}.e%j
		#SBATCH --time=${TIME}:00
		#SBATCH --output=/dev/null
		#SBATCH --partition=${QUEUE}
		#SBATCH --mail-user=$(whoami)@auburn.edu
		#SBATCH --mail-type=NONE
		#SBATCH --hint=nomultithread 
		${REQUEUE_STR}
		WRKDIR=\$(pwd)
		FNAME=${FNAME}
		SCRDIR=${SCRDIR}
		SUBDIR=${SUBDIR}
		NPROC=${NPROC}
	EOF
}
G16_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		set env OMP_NUM_THREADS=${THREADS}
		module -q load gaussian/16
		export g16root=\$(which g16 | sed -e "s/\\/g16\\/g16$//g")
		. \${g16root}/g16/bsd/g16.profile
		export GAUSS_SCRDIR=\${SCRDIR}
		export GAUSS_CDEF=\${NPROC}
		export GAUSS_MDF=${MEM_PROC}${MEM_UNIT}
		cp \${WRKDIR}/${FNAME}.inp \${SCRDIR}/${FNAME}.inp
		cd \${SCRDIR}
		g16 < \${SCRDIR}/${FNAME}.inp >& ${WRKDIR}/${FNAME}.log
	EOF
}
Closer_Gen(){
	cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
		if [[ ! -s \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} ]]; then
		rm -f \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID}; else
		mv \${SUBDIR}/\${FNAME}.e\${SLURM_JOB_ID} \${WRKDIR}/. ; fi
		exit 0
	EOF
}
File_Editor(){
	#cat >> ${SUBDIR}/${FNAME}.batch <<- EOF
	sed -i s/%chk=[[:graph:]]*/%chk=${FNAME}.chk/ ${FNAME}.inp
	#EOF
}
Old_Handler(){
	NPROC=$2
	TIME="$3:$4"
}
CPU_Handler(){
	if [[ ${NPROC_CUSTOM} -eq 1 ]]; then 
	## Assign CPU request within input file ##
		if [[ $(grep -ic '%NProcShared' ${FNAME}.inp) -ge 1 ]]; then
			sed -i '/^%[nN][pP][rR][oO][cC][sS][hH][aA][rR][eE][dD]/d' ${FNAME}.inp
			sed -i "2i %NProcShared=${NPROC}" ${FNAME}.inp
		else
			sed -i "2i %NProcShared=${NPROC}" ${FNAME}.inp
		fi
	fi
	if [[ ${NPROC_CUSTOM} -ne 1 ]]; then
		if [[ $(grep -ic -m 1 '^%NProcShared' ${FNAME}.inp) -eq 1 ]]; then 
			NPROC=$(grep -i -m 1 '^%NProcShared' ${FNAME}.inp | awk -F'=' '{print $2}')
		elif [[ $(grep -ic -m 1 '^%NProcShared' ${FNAME}.inp) -gt 1 ]]; then 
			echo"Error in input: You have too many %NProcShared lines."
		else
			echo"Error in input: %NProcShared line not found."
		fi
	fi
## Remove %CPU Flag
	if [[ $(grep -ic '%CPU' ${FNAME}.inp) -gt 1 ]]; then
		sed -i '/^%[cC][pP][uU]=/d' ${FNAME}.inp
	fi
}
Mem_Handler(){ 
	if [[ ${MEM_CUSTOM} -eq 1 ]]; then 
		MEM_PROC=$(( ${MEM_JOB} * 10 / 12 ))
    if [[ $(grep -ic '%mem' ${FNAME}.inp ) -ge 1 ]]; then
      sed -i '/^%[mM][eE][mM]=/d' ${FNAME}.inp
      sed -i "3i %MEM=${MEM}GB" ${FNAME}.inp
    else
      sed -i "3i %MEM=${MEM}" ${FNAME}.inp
    fi
	else
		if [[ -n $(grep -i -m 1 '%mem' ${FNAME}.inp ) ]]; then
			MEM=$(grep -i -m 1 '%mem' ${FNAME}.inp | awk -F'=' '{print $2}')
			MEM_UNIT=$(echo ${MEM} | sed -e 's/[[:digit:]]*//')
			MEM_VAL=$(echo ${MEM} | sed -e "s/${MEM_UNIT}//")
			case ${MEM_UNIT} in
				[kK][bB])MEM_BYTES=$((${MEM_VAL}*1024));;
				[mM][bB])MEM_BYTES=$((${MEM_VAL}*1024*1024));;
				[gG][bB])MEM_BYTES=$((${MEM_VAL}*1024*1024*1024));;
			esac
			MEM_PROC=$(( ${MEM_BYTES}/1024/1024/1024 ))
			MEM_JOB=$(( ${MEM_PROC} * 12 / 10 ))
		else
			echo "You did not specify a memory request in your input file"
			exit 60
		fi
	fi
}
Maint_Check(){ #This isn't correctly working currently. Fix this, silly-head.
	Queue_Limit=$(/tools/scripts/max_walltime.sh | grep 'Wall-time (hours)' | awk -F: '{print $2}' | sed 's/ //') 
	Time_Req=$( Round_Up $( echo ${TIME} | awk -F: '{print $1  * 60 +  $2 }') )
	if [[ -s Queue_Limit ]] && [[ $(( ${Queue_Limit} * 60 )) -lt ${Time_Req} ]]; then TIME="${Queue_Limit}:00"; fi 
}
Queue_Set(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case ${QTYPE} in
		[bB]2) echo "bigmem2";;
		[rR][bB]2) echo "ezm0048_bg2";;
		[bB]4) echo "bigmem4";;
		[a]) echo "amd";;
		[Gg][Pp][Uu]) echo "gpu2";;
		[rR]) echo "ezm0048_std";;
		[nN]) echo "nova";;
		*) echo "general";;
	esac
}
Req_Check(){
	QTYPE=$( echo $QTYPE | awk '{print tolower($0)}' )
	case $QTYPE in
		rb2 | b2 ) NMAX=48; MEMMAX=384;;
		b4) NMAX=48; MEMMAX=768;;
		a | amd) NMAX=128; MEMMAX=256;;
		gpu2 | gpu4) echo "This script is not set up for GPU calculations- please resubmit with another queue"; exit 30 ;;
		s | * ) NMAX=48; MEMMAX=192;;
	esac
	if [[ ${NODE_LIMIT} -eq 1 ]]; then
		if [[ ${NPROC} -gt ${NMAX} ]]; then echo "You have requested more processors than is available on this node (${NMAX})"; exit; fi
		if [[ ${MEM_JOB} -gt ${MEMMAX} ]]; then echo "You have requested more memory than is available on this node (${MEMMAX})"; exit; fi
	else
		if [[ ${NPROC} -gt ${NMAX} ]]; then NODES_NPROC=$( Div_Rounder "${NPROC}" "${NMAX}" ); fi
		if [[ ${MEM_JOB} -gt ${MEMMAX} ]]; then NODES_MEM=$( Div_Rounder "${MEM_JOB}" "${MEMMAX}" ); fi
		if [[ ${NODES_NPROC} -gt ${NODES_MEM} ]]; then NODES=${NODES_NPROC};
			elif [[ ${NODES_MEM} -gt ${NODES_NPROC} ]]; then NODES=${NODES_MEM};
			else NODES=1; fi
	fi 
	if [[ ${NODES} -eq 1 ]]; then MEM_STR="#SBATCH --mem=${MEM_JOB}GB";
		else MEM_STR="#SBATCH --mem-per-cpu=$( Div_Rounder "${MEM_JOB}" "$(( ${NPROC} - 1))" )GB"
	fi	
	#Set up a handler for controlling tasks per node here
	#SBATCH --ntasks-per-node=; 
	NTASKS_STR="#SBATCH --ntasks=${NPROC}"	
	NODE_STR="#SBATCH --nodes=${NODES}"
	THRD_STR="#SBATCH --cpus-per-task=${THREADS}"
}
Helpfn(){
echo "
You have run the g16b job submission script for Gaussian 16. This script will automatically create a batch job for you. 

The output files will automatically be placed in the current directory.
Input files must be of the form:  [file].inp
Output files will be of the form: [file].out

      Options:
       -h    |   Help, display this current usage guide
       -n    |   Number of Processors Requested- This is optional as you can specify processor requests
             |      in your input file
       -m    |   Memory Requested in GB; Specifying the GB units is optional- This is optional as you can specify  
             |      memory requests in your input file
       -t    |   Time Limit for Jobs in HR:MIN format
       -N    |   Number of nodes to run on; this is unnecessary as Gaussian 16 can only run on a single node 
       -q    |   Which queue this job will be submitted to; Options: b2- bigmem2, rb2- Investor bigmem2, b4-bigmem4, a-amd,
             |      gpu-GPU2, r-Investor general, g- general nodes       

You may specify these in any order, but the filename must be the last value specified. 

Your current defaults are:
    Proc         =  Determined by input file if not specified
    Time         =  ${TIME}
    Queue        =  ${QTYPE}/$(Queue_Set)
    REQUEUE_OPT  =  ${REQUEUE_OPT}   | 1 if you want to allow jobs to requeue, 0 disabled
    FILE_EDIT    =  ${FILE_EDIT}   | 1 to autorename your .chk file in the input file, 0 disabled       
If -n, -m, -t, -N, and -q are not specified default values will be used.

You can change this in $(echo $0)

EXAMPLE:
$(echo $0) -n 12 -t 10:00 -q b2 -m 48GB file.inp 
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
