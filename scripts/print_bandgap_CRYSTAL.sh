#!/bin/bash

CRYSTALOutPattern="*.out"



print_usage() {
	echo ""
	echo "Usage: print_bandgap_CRYSTAL" 
	echo "       print_bandgap_CRYSTAL file_name"
	echo "       print_bandgap_CRYSTAL directory_name"
	echo "       print_bandgap_CRYSTAL [-f file_name] [-h] [-r]"
	echo "       print_bandgap_CRYSTAL [-f directory_name] [-h] [-r]"
	echo ""
}

	
# print in constant width columns
help_fmt=" %-20s%s\n"
print_help() {
	print_usage

	echo "positional arguments:"
	printf "$help_fmt" "file_location" "Either the .out file or the directory in which it is located."

	echo "optional arguments:"
	printf "$help_fmt" "-f" "Either the .out file or the directory in which it is located."
	printf "$help_fmt" "-h" "Print this help message and exit."
	printf "$help_fmt" "-r" "Perform command recursively on every .out file in every subdirectory."
	echo ""
}

print_bandgap_information() {
	MyCRYSTALOut="$1"
	MaxSteps=$(grep "MAXIMUM ALLOWED NUMBER OF STEPS" $MyCRYSTALOut | tr -s ' ' | cut -f 7 -d " ")
	CountOPTGEOM=$(grep OPTGEOM $MyCRYSTALOut -c )
	GeometryOptimizationConverged=$(grep "OPT END - CONVERGED" $MyCRYSTALOut -c )
	TotalEnergyCount=$(grep "TOTAL ENERGY"  $MyCRYSTALOut -c )
	MaxPrintETOT=10

	echo ""
	echo "Checking on $MyCRYSTALOut"
	
	if [[ ! -z "$MaxSteps" && "$(echo 'BAD AND')" && "$MaxSteps" -gt 1 &&  "$CountOPTGEOM" -gt 0 ]]; then 
		GeometryOptimization=true
		echo "Alert: Geometry optimization detected. This file might not contain final bandgap so I will not print anything. "
	else
		"${SALSA_DIR}/Scripts/extract_CRYSTAL_bandgap.py" -f "$MyCRYSTALOut"
	fi

}

# Only Functions above this line -------------------------------------------------------


MyCRYSTALOutLocation="$1"

# parse single character flags
# for more info see: stackoverflow.com/a/21128172/7839195
# default flag values
recursive=false

while getopts 'hf:r' flag; do
  case "${flag}" in
	f) MyCRYSTALOutLocation=$OPTARG
	;;

	r) recursive=true
	;;
	
	h) print_help
	exit 0 
	;;
	
	*) print_usage
	exit 1 
	;;
  esac
done



# First check if directly given the file
# This supersedes the -r flag
if [[ -f "$MyCRYSTALOutLocation" ]]; then
	MyCRYSTALOutList=("$MyCRYSTALOutLocation")
else
	# Parse commandline argument to determine directory
	if [[ -d "$MyCRYSTALOutLocation" ]]; then
		MyCRYSTALDir=$MyCRYSTALOutLocation
	else
		# The following alert does not input if the file_location parameter was left blank
		if [ ${#MyCRYSTALOutLocation} -ne 0 ]; then	    
		echo "Could not find ${MyCRYSTALOutLocation}. Searching current directory instead."
		fi
		MyCRYSTALDir='.'	    
	fi
	
	# Collect the requested out files and check there is the correct number
	if [ $recursive = true ]; then
		MyCRYSTALOutList=($(  find $MyCRYSTALDir -name "$CRYSTALOutPattern"))
	else
		MyCRYSTALOutList=($(  find $MyCRYSTALDir -maxdepth 1 -name "$CRYSTALOutPattern"  ))
	fi
	MyCRYSTALOutCount="${#MyCRYSTALOutList[@]}"
	if [ "$MyCRYSTALOutCount" -eq 0 ]; then
		echo -e "\nCould not find CRYSTAL output file.\n"
		exit 2
	elif [ "$MyCRYSTALOutCount" -gt 1 -a "$recursive" = false ]; then
		echo -e "\nCould not determine which CRYSTAL output file to use. Please specify one:"
		# ls -tr $MyCRYSTALDir/$CRYSTALOutPattern
		echo  "${MyCRYSTALOutList[@]}"
		echo ""
		exit 3
	fi

fi

for MyCRYSTALOut in ${MyCRYSTALOutList[@]}; do
	print_bandgap_information "$MyCRYSTALOut"
done





