#!/bin/bash
# Completed on Mar 15 2023
# author: Sean Stafford


# quiet flag implemented following method 2 from stackoverflow.com/a/36003000/7839195
BeQuiet() { 
	exec 6>&1
	exec > /dev/null # redirect stdout to /dev/null (trash it)
} # stop printing to terminal 
SpeakUp() { exec 1>&6 6>&- ; } # resume printing to terminal

TimeStamp() {
	date +"%T %Y-%m-%d"
}

print_usage() {
	echo ""
	echo "Usage: setup_project.sh project_name" 
	echo "       setup_project.sh -n project_name [-U USPEX_input_directory] [-q]"
	echo "       setup_project.sh -h "
	echo ""
}


help_fmt=" %-25s%s\n"
print_help() {
	print_usage

	echo "positional arguments:"
	printf "$help_fmt" "project_name" "Name of new project" 


	echo "optional arguments:"
	printf "$help_fmt" "-n project_name" "Name: Name of new project" 
	printf "$help_fmt" "-U USPEX_input_directory" "Directory: Example directory to use as template for USPEX calculations. A default relative directory can also be saved in Scripts/defaults.json" 
	printf "$help_fmt" "-q" "Quiet: Don't send anything to stdout" 
	
}

# default flag values
quiet=false
project_name=""
USPEX_input_directory=""

# parse single character flags
# for more info see: stackoverflow.com/a/21128172/7839195
while getopts 'n:U:qh' flag; do
  case "${flag}" in

	n) project_name=$OPTARG
	;;

	U) USPEX_input_directory=$OPTARG
	;;

	q) quiet=true
	BeQuiet
	;;

	h) print_help
	exit 0 
	;;
	
	*) print_usage
	exit 1 
	;;
  esac
done

if [[ "$project_name" == "" ]]; then
	project_name="$1"
fi

if [[ "$USPEX_input_directory" == "" ]]; then
	if [[ -f "${SALSA_DIR}/Scripts/defaults.json" ]]; then
		USPEX_input_directory="${SALSA_DIR}/$(jq -r '.USPEX_input_directory' "${SALSA_DIR}/Scripts/defaults.json" )"
	fi
fi

# Only functions and option parsing above this line -------------------------------------------------------

project_directory="${SALSA_DIR}/Projects/${project_name}"
now="$(TimeStamp)"

if [[ -d "$project_directory" ]]; then
    echo Cannot setup a project named \""$project_name"\" because "$project_directory" already exists.
    exit 2
elif ! [[ -d "$USPEX_input_directory" ]] && ! [[  "$USPEX_input_directory" == "" ]]; then
    echo Cannot setup \""$project_name"\" using $USPEX_input_directory for USPEX input, because it does not exist.
else
    echo Setting up a project named \""$project_name"\".
    mkdir -p "${project_directory}"
    touch "${project_directory}/log"
    echo "SALSA project log for $project_name" >> "${project_directory}/log" 
    cat "${SALSA_DIR}/Scripts/banner.txt" >> "${project_directory}/log"
    echo "Project set up at $now" >> "${project_directory}/log" 
    cp "${SALSA_DIR}/Scripts/empty_inventory.csv" "${project_directory}/inventory.csv"
    mkdir -p "${project_directory}/USPEX/inputs"
    if ! [[  "$USPEX_input_directory" == "" ]]; then
        cp -r $USPEX_input_directory/* "${project_directory}/USPEX/inputs"
        echo -e "Created USPEX calculation template with directory tree:\nUSPEX/inputs" >> "${project_directory}/log"
        tree "${project_directory}/USPEX/inputs" | tail -n +2 >> "${project_directory}/log"
    else
        mkdir -p "${project_directory}/USPEX/inputs"
        echo "Created empty USPEX calculation template directory" >> "${project_directory}/log" 
    fi
    mkdir -p "${project_directory}/CRYSTAL/inputs"
fi

echo Project log printout:
cat "${project_directory}/log"
