#!/bin/bash

# Completed on March 25 2023
# Author: Sean Stafford


print_usage() {
	echo ""
	echo "Usage: USPEX_status_check [input_file(s)] [input_directory(s)]" 
	echo "       USPEX_status_check -f in_file [-k DONE_kw] [-o out_extension] [-s submission_extension] [-i in_extension]"
	echo "       USPEX_status_check -d directory_depth [-p parent_directory] [-k DONE_kw] [-o out_extension] [-s submission_extension] [-i in_extension]"
	echo "       USPEX_status_check -h "
	echo ""
}


help_fmt=" %-25s%s\n"
print_help() {
	print_usage

	echo "positional arguments:"
	printf "$help_fmt" "input_list" "List of files and/or directories to check. If nothing given, look in '.' for files with input extension." 

	echo "optional arguments:"
	printf "$help_fmt" "-f in_file"  "Single input file tp check. If this flag is given, -d and -p flags are ignored."
	printf "$help_fmt" "-d directory_depth"  "Directory depth at which to check all statuses."
	printf "$help_fmt" "-p parent_directory" "Directory from which to search at some depth. Default is '.'."
	printf "$help_fmt" "-k DONE_keyword"  "Keyword which, if found in an out file, indicates the status is DONE. Default is 'TOTAL CPU TIME'."
	printf "$help_fmt" "-o out_extension"  "Extension of CRYSTAL out files. Default is '.out'."
	printf "$help_fmt" "-s submission_extension"  "Extension of CRYSTAL submission files. Default is '.slurm'."
	printf "$help_fmt" "-i in_extension"  "Extension of CRYSTAL input files. Default is '.d12'."
#	printf "$help_fmt" "-e exclude_status"   "Status(es) to exclude in printed results. Use format 'status1|status2' to exclude multiple statuses."
	printf "$help_fmt" "-h" "Print this help message and exit."
	echo ""
}

# default flag values
DONE_kw="TOTAL CPU TIME"
submission_extension=".slurm"
out_extension=".out"
in_extension=".d12"

# parse single character flags
# for more info see: stackoverflow.com/a/21128172/7839195
while getopts ':f:d:p:k:o:s:i:h' flag; do
  case "${flag}" in
	f) in_file=$OPTARG
	;;

	d) directory_depth=$OPTARG
	;;

	p) parent_directory=$OPTARG
	;;

	k) DONE_kw=$OPTARG
	;;

	o) out_extension=$OPTARG
	;;

	s) submission_extension=$OPTARG
	;;

	i) in_extension=$OPTARG
	;;

#	e) exclude_status=$OPTARG
#	;;
#
	h) print_help
	exit 0 
	;;
	
	*) print_usage
	exit 1 
	;;
  esac
done

Max () {
	arr=("$@")
	IFS=$'\n'
	echo "${arr[*]}" | sort -nr | head -n1
}

TimeSinceModified () {
	lastModificationSeconds=$(date -r $1 +%s)
	currentSeconds=$(date +%s)
	echo $((currentSeconds - lastModificationSeconds))
}	


CheckStatus () {
	infile=$1
	outfile="${infile/\.d[0-9]*/$out_extension}"
	subfile="${infile/\.d[0-9]*/$submission_extension}"
	calcname=$(basename $1)

	if [[ ! -f $outfile ]]; then
		if ! [ -f $infile ] || ! [ -f $subfile ]; then
			status="Files_Missing"
		else
			status="Waiting"
		fi
	elif grep -q "$DONE_kw" $outfile; then
		status="DONE"
	else
		timed_out_str="TIME LIMIT"
		timesincemod=$(TimeSinceModified $outfile)
		haltedthresh=7200
		if $( tail -n 1 $outfile | grep -q  "$timed_out_str"); then
			status="Timed_Out"
		elif [[ $timesincemod -gt $haltedthresh ]]; then
			status="Stalled"
		else
			status="Running"
		fi
	fi
	
	echo $status		
}

# -------------------------------------------------------------------------------------------------------------------
# End of functions
# -------------------------------------------------------------------------------------------------------------------

if [ ! -z $in_file ]; then
	in_list=( "$in_file" )
elif [ ! -z $directory_depth ]; then
	if [ ! -z $parent_directory ]; then
		cd $parent_directory
	fi
	in_list=( )
	for calc_dir in $(find . -mindepth $directory_depth -maxdepth $directory_depth -type d ); do 
		in_list=( ${in_list[@]} "$(ls $calc_dir/*${in_extension} 2>/dev/null )" )
	done
else
	if [ "$1" == "" ]; then
		in_list=( "$(ls *${in_extension}  2>/dev/null )" )
	else
		in_list=( )
		for f in  "$@" ; do 
			if [[ -d "$f" ]]; then
				in_list=(${in_list[@]} "$(ls $f/*${in_extension} 2>/dev/null )" )
			else
				in_list=(${in_list[@]} "$f" )
			fi
		done
	fi
fi

max_in_length=$(( $(printf "%s\n" "${in_list[@]}" | wc -L )  + 2 ))
printout_fmt=" %-${max_in_length}s%s\n"

for f in ${in_list[@]}; do
	if [[ -f $f ]]; then
		status=$( CheckStatus "$f")
	else
		status=Nonexistant
	fi

	printf $printout_fmt $f $status
	
done
