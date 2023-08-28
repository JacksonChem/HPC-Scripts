#!/bin/bash

Main(){
	NUM_REPEAT=5 #Number of dependent job submissions
	SPLIT_OUTPUTS=false #Enable seperate outputs for each job
	CREATE_BACKUPS=false #Create a backup folder when a job terminates-not implemented yet
	INITIAL_CALCULATION=false #First job starts with [fname].inp1 rather than [fname].inp
	SPLIT_CNT=1 #Starting count for the split outputs

	if [[ "$#" -eq 1 && "$1" != "-h" ]]; then BATCH=$1; else Option_Handler "$@"; fi
	if [[ -z ${BATCH} ]]; then echo "No batch submission file specified"; exit; fi	
	if [[ -n ${JOB_TO_FOLLOW} ]]; then
		for ((SUB_CNT=1; SUB_CNT<=NUM_REPEAT; SUB_CNT++)); do
			if [[ ${SUB_CNT} -eq 1 ]]; then
				JOB_SUB=$(sbatch --depend=${JOB_TO_FOLLOW} ${BATCH}) 
			else
				JOB_NUM=$(echo ${JOB_SUB} | awk '{printf "%8d", $4}')
				JOB_SUB=$(sbatch --depend=${JOB_NUM} ${BATCH})
			fi
		done
		exit
	fi

	if ${SPLIT_OUTPUTS}; then
		Many_Outputs;
	else
		One_Output;
	fi
}
Option_Handler(){
	while getopts ":hb:n:sS:kij:" option; do
		case $option in
			h) Helpfn; exit;;  #Call help function and exit
			b) BATCH=$OPTARG;; #The name of your slurm submission file
			n) NUM_REPEAT=$OPTARG;; #Number of Dependent Submissions
			s) SPLIT_OUTPUTS=true;; #Enable seperate outputs for each job
			S) SPLIT_CNT=$OPTARG; SPLIT_OUTPUTS=true;; #Specify ouput start count & enable seperate outputs 
			B) CREATE_BACKUPS=true;;  #Create a backup folder when a job terminates-not implemented yet
			i) INITIAL_CALCULATION=true;; #First job starts with [fname].inp1 rather than [fname].inp
			j) JOB_TO_FOLLOW=$OPTARG;; #Set jobs to depend on a preexisting job
			esac
	done
}
One_Output(){
	for ((SUB_CNT=1; SUB_CNT<=NUM_REPEAT; SUB_CNT++)); do
		if [[ ${SUB_CNT} -eq 1 ]]; then
			Initial_Job;
		else
			JOB_NUM=$(echo ${JOB_SUB} | awk '{printf "%8d", $4}')
			JOB_SUB=$(sbatch --depend=${JOB_NUM} ${BATCH})
		fi
	done
}

Many_Outputs(){
	SPLIT_MAX=$((${SPLIT_CNT}+${NUM_REPEAT}))
	for i in $(seq -w ${SPLIT_CNT} ${SPLIT_MAX}); do
		sed -i "s/out[0-9]*/out$i/" ${BATCH} 
		if [[ ${i} -eq ${SPLIT_CNT} ]]; then
			Initial_Job;
		else
			JOB_NUM=$(echo ${JOB_SUB} | awk '{printf "%8d", $4}')
			JOB_SUB=$(sbatch --depend=${JOB_NUM} ${BATCH})
		fi
	done
}
Initial_Job(){
	if ${INITIAL_CALCULATION}; then
		sed -i "s/inp[0-9]* /inp1 /" ${BATCH}
		JOB_SUB=$(sbatch ${BATCH})
		sed -i "s/inp1 /inp /" ${BATCH}
	else
		JOB_SUB=$(sbatch ${BATCH})
	fi
}
Helpfn(){
echo "
You have run the dep-gen script. This script will generate and submit dependent slurm sbatch jobs for you.

An initial sbatch submission file is prerequisite and must be specified. 
 Options:
 Flag   Arg.  | Description  
  -h    N/A   | Help, display this current usage guide
  -b  <FILE>  | (Required) Specify the name of your sbatch submission file
  -j  <JOBID> | (Optional) Specify a slurm jobid that the first submitted job will depend on
  -n   <int>  | (Optional) Specify the total number of slurm jobs to submit; default is ${NUM_REPEAT}
  -s    N/A   | (Optional) Enables seperate output files for each slurm job
  -S   <int>  | (Optional) Enables seperate output files for each slurm job and specifies the starting count
  -B    N/A   | (Optional) Enables the option to create a backup directory at the end of each job- NOT CURRENTLY IMPLEMENETED 

You may also run this script by simplying calling it and specifying only the batch file.
"
}
Main "$@"; exit
