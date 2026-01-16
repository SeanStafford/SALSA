# scripts

Shell scripts for HPC job management and project setup.

## Status Monitoring

### USPEX_status_check

Monitor USPEX calculation status across multiple directories.

```bash
# Check single calculation
USPEX_status_check calculation_directory

# Check all calculations at depth 2
USPEX_status_check -d 2 -p /path/to/projects

# Exclude completed calculations from output
USPEX_status_check -d 2 -e "DONE"
```

### CRYSTAL_status_check.sh

Monitor CRYSTAL calculation status. Checks for completion keyword in output files.

```bash
# Check specific files or directories
CRYSTAL_status_check.sh input1.d12 input2.d12

# Check all at directory depth
CRYSTAL_status_check.sh -d 2 -p /path/to/projects
```

## Project Setup

### setup_project.sh

Initialize directory structure for a new SALSA project.

### compile_POTCARs_locally.sh

Compile element-specific VASP POTCAR files from the reference library.

## Utilities

### reset_USPEX.sh

Reset a USPEX calculation directory to restart from scratch.

### parse_inventory

Parse and query the inventory CSV.

### print_bandgap_CRYSTAL.sh

Extract and display bandgap from CRYSTAL output files.
