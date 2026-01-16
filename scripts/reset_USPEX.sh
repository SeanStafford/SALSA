#!/bin/bash



print_usage() {
	echo ""
	echo "Usage: reset_USPEX.sh"
	echo "       reset_USPEX.sh USPEX_directory" 
	echo "       reset_USPEX.sh -h "
	echo ""
}


help_fmt=" %-25s%s\n"
print_help() {
	print_usage

	echo "positional arguments:"
	printf "$help_fmt" "USPEX_directory" "USPEX directory. Default is "."." 

	echo "optional arguments:"
	printf "$help_fmt" "-h" "Print this help message and exit."
	echo ""
}

# parse single character flags
# for more info see: stackoverflow.com/a/21128172/7839195
while getopts ':h' flag; do
  case "${flag}" in
	h) print_help
	exit 0 
	;;
	
	*) print_usage
	exit 1 
	;;
  esac
done

if [[ $1 == "" ]]; then
	USPEX_directory=.
else
	if [[ -d $1 ]]; then
		USPEX_directory=$1
	else
		echo Directory $1 does not exist. Nothing to reset.
		exit 1
	fi
fi

cd $USPEX_directory

results_exist=FALSE
for f in results*/*dividuals* ; do
	if [[ -f $f ]]; then
		results_exist=TRUE
	fi
done
for f in results*/*struc* ; do
	if [[ -f $f ]]; then
		results_exist=TRUE
	fi
done
for f in results*/*BEST* ; do
	if [[ -f $f ]]; then
		results_exist=TRUE
	fi
done

if [[ $results_exist == TRUE ]]; then
	echo Results appear to exist in $(pwd). This script refuses to reset for fear of deleting something useful.
	exit 2
else
	is_not_USPEX_directory=FALSE
	if [[ ! -f INPUT.txt ]]; then
		is_not_USPEX_directory=TRUE
	elif [[ ! -f log ]]; then
		is_not_USPEX_directory=TRUE
	fi
	
	if [[ $is_not_USPEX_directory == TRUE ]]; then
		echo Cannot verify that $(pwd) is a USPEX directory. This script refuses to proceed for fear of deleting something useful.
		exit 3
	else
		if [[ -f reset_USPEX.sh ]]; then
			chmod -w reset_USPEX.sh
		fi
		
		mkdir PRESERVE
		mv -f INPUT.txt PRESERVE/
		mv -f USPEX_submission.slurm PRESERVE/
		find . -mindepth 1 -maxdepth 1 -writable -type f -exec rm {} +
		rm -r results*
		rm -r Calc*
		cp -f PRESERVE/* .
		rm -rf PRESERVE
		echo Reset USPEX directory $(pwd) with reset_USPEX.sh script.
	fi
fi
