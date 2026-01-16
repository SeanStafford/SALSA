"""Main workflow orchestration for SALSA pipeline.

This module contains the InventoryRow class which manages the state machine
for propagating compounds through USPEX structure prediction and CRYSTAL
DFT calculations.
"""

import os
import re
import subprocess
from typing import Dict, List

import pandas as pd

from salsa.uspex.structure import save_best_USPEX_structure
from salsa.utils.serialization import dict_to_str, generate_unique_id, str_to_dict
from salsa.utils.timestamp import get_file_timestamp, get_time

# Inventory CSV columns for tracking compound calculations
INVENTORY_COLUMNS = [
    "index",
    "compound_name",
    "compound_ID",
    "composition_dictionary",
    "source",
    "status",
    "interpolated_property_dictionary",
    "interpolated_properties_in_target_region",
    "interpolated_properties_in_ideal_region",
    "parent_1_compound_name",
    "parent_1_fraction",
    "parent_1_property_dictionary",
    "parent_2_compound_name",
    "parent_2_fraction",
    "parent_2_property_dictionary",
    "USPEX_started",
    "new_USPEX_started",
    "USPEX_directory",
    "USPEX_archive_directory",
    "USPEX_status",
    "USPEX_update_timestamp",
    "USPEX_max_percent_done",
    "USPEX_min_jobs_remaining",
    "USPEX_current_generation",
    "USPEX_generation_streak",
    "stalled_in_USPEX",
    "USPEX_done",
    "USPEX_best_structure",
    "USPEX_best_enthalpy",
    "USPEX_best_property_dictionary",
    "USPEX_status_update_timestamp",
    "CRYSTAL_started",
    "new_CRYSTAL_started",
    "CRYSTAL_directory",
    "CRYSTAL_input_file",
    "CRYSTAL_archive_directory",
    "CRYSTAL_status",
    "CRYSTAL_SLURM_job_ID",
    "CRYSAL_update_timestamp",
    "CRYSTAL_done",
    "CRYSTAL_output_structure",
    "CRYSTAL_output_energy",
    "CRYSTAL_output_property_dictionary",
    "CRYSTAL_properties_in_target_region",
    "CRYSTAL_properties_in_ideal_region",
    "CRYSTAL_status_update_timestamp",
    "champion_compound",
    "row_last_updated",
]


class InventoryRow:
    """Manages a single compound through the SALSA workflow.

    This class implements the state machine that propagates a compound from
    initial candidate through USPEX structure prediction and CRYSTAL DFT
    calculations.

    The workflow states are:
        new_candidate_compound -> USPEX(Waiting) -> USPEX(Submitted) ->
        USPEX(Running) -> USPEX(DONE) -> CRYSTAL(1_Waiting) ->
        CRYSTAL(1_Submitted) -> ... -> CRYSTAL(N_DONE) -> DONE

    Attributes:
        compound_name: Chemical formula of the compound.
        compound_ID: Unique identifier for this calculation.
        calculation_name: Combined name_ID for directory naming.
        status: Current workflow status.
        composition_dictionary: Element counts for the compound.
    """

    def __init__(self, pd_series: pd.Series):
        """Initialize from a pandas Series (inventory row).

        Args:
            pd_series: Row from inventory DataFrame.
        """
        self.import_attributes_from_existing_row(pd_series)

    def generate_new_id(self, ID_list: List[str], extant_IDs: List[str]) -> None:
        """Generate a unique compound ID.

        Args:
            ID_list: List of existing IDs to avoid.
            extant_IDs: Global list to append new ID to.
        """
        self.compound_ID = ""
        while self.compound_ID in list(ID_list) + [""]:
            self.compound_ID = generate_unique_id()
        self.calculation_name = self.compound_name + "_" + self.compound_ID
        print(f"Assigned calculation_name {self.calculation_name} at {get_time()}")
        extant_IDs.append(self.compound_ID)

    def import_attributes_from_existing_row(self, pd_series: pd.Series) -> None:
        """Import attributes from an existing inventory row.

        Args:
            pd_series: Row from inventory DataFrame.
        """
        for key, value in pd_series.items():
            if value != "":
                if "dictionary" in key:
                    self.__setattr__(key, str_to_dict(value, value_type="str"))
                else:
                    if type(value) is int:
                        value = str(value)
                    self.__setattr__(key, value)

    def propagate(
        self,
        ID_list: List[str],
        extant_IDs: List[str],
        project_dir: str,
        USPEX_input_directory: str,
        POTCAR_reference_directory: str,
        USPEX_check_status_script: str,
        CRYSTAL_input_directory: str,
        CRYSTAL_check_status_script: str,
    ) -> None:
        """Advance the compound through the workflow.

        This is the main state machine driver that determines what action
        to take based on current status.

        Args:
            ID_list: List of existing compound IDs.
            extant_IDs: Global list of IDs (modified in place).
            project_dir: Base project directory.
            USPEX_input_directory: Path to USPEX input templates.
            POTCAR_reference_directory: Path to POTCAR files.
            USPEX_check_status_script: Path to USPEX status check script.
            CRYSTAL_input_directory: Path to CRYSTAL input templates.
            CRYSTAL_check_status_script: Path to CRYSTAL status check script.
        """
        new_inventory_entry = False
        if not hasattr(self, "compound_ID"):
            new_inventory_entry = True
            self.generate_new_id(ID_list, extant_IDs)

        if not hasattr(self, "source"):
            self.status = "Stalled because source undefined"
            print(
                f"Cannot propagate compound {self.compound_name} ({self.compound_ID}) "
                "without 'source' information."
            )
            return

        if new_inventory_entry:
            if self.source == "new_candidate_compound":
                self.setup_USPEX(project_dir, USPEX_input_directory, POTCAR_reference_directory)
        else:
            if "USPEX" in self.status:
                self.propagate_USPEX(
                    project_dir,
                    USPEX_check_status_script,
                    CRYSTAL_input_directory,
                )
            elif "CRYSTAL" in self.status:
                self.propagate_CRYSTAL(CRYSTAL_input_directory, CRYSTAL_check_status_script)

    def setup_USPEX(
        self,
        project_dir: str,
        USPEX_input_directory: str,
        POTCAR_reference_directory: str,
    ) -> None:
        """Initialize USPEX calculation directory.

        Creates calculation directory, copies templates, and configures
        input files with compound-specific parameters.

        Args:
            project_dir: Base project directory.
            USPEX_input_directory: Path to USPEX input templates.
            POTCAR_reference_directory: Path to POTCAR files.
        """
        USPEX_directory = f"{project_dir}/USPEX/{self.calculation_name}"
        os.makedirs(USPEX_directory, exist_ok=True)
        self.USPEX_directory = USPEX_directory

        os.system(f"cp -r {USPEX_input_directory}/* {self.USPEX_directory}/")

        for rootdir, dirs, files in os.walk(self.USPEX_directory):
            for f in files:
                path = rootdir + "/" + f

                # Configure INCAR files
                if "INCAR" in f:
                    os.system(f"sed -i 's/CALCULATION_NAME/{self.calculation_name}/g' {path}")

                # Configure INPUT.txt with composition
                if "INPUT.txt" in f:
                    atom_types_string = " ".join(self.composition_dictionary.keys())
                    num_species_string = " ".join(
                        [str(v) for v in self.composition_dictionary.values()]
                    )
                    os.system(f"sed -i 's/ATOM_TYPES/{atom_types_string}/g' {path}")
                    os.system(f"sed -i 's/NUM_SPECIES/{num_species_string}/g' {path}")

                # Configure submission scripts
                if "submitJob_local.py" in f:
                    os.system(f"sed -i 's/CALCULATION_NAME/{self.calculation_name}/g' {path}")
                if "USPEX_submission.slurm" in f:
                    os.system(f"sed -i 's/CALCULATION_NAME/{self.calculation_name}/g' {path}")

        # Copy POTCAR files for each element
        for element in self.composition_dictionary.keys():
            potcar_path = f"{POTCAR_reference_directory}/POTCAR_{element}"
            if os.path.isfile(potcar_path):
                os.system(f"cp {potcar_path} {self.USPEX_directory}/Specific/")
            else:
                print(
                    f"Cannot begin USPEX calculation {self.calculation_name} "
                    f"because no '{potcar_path}' could be located."
                )
                self.status = "Stalled because POTCAR missing"

        self.USPEX_status = "Waiting"
        self.status = "USPEX(Waiting)"
        self.USPEX_update_timestamp = get_file_timestamp(self.USPEX_directory)
        print(
            f"USPEX calculation directory {self.calculation_name} "
            f"created at {self.USPEX_update_timestamp}"
        )
        self.USPEX_status_update_timestamp = get_time()

    def parse_USPEX_status_check(self, output_lines: List[str]) -> None:
        """Parse output from USPEX status check script.

        Args:
            output_lines: Lines from status check script output.
        """
        for line in output_lines:
            if "This optimization is " in line:
                self.USPEX_max_percent_done = line.split("at most ")[1].split(" ")[0]
                self.USPEX_min_jobs_remaining = line.split("at least ")[1].split(" ")[0]
            elif "This is currenly on generation" in line:
                self.USPEX_current_generation = line.split("generation ")[1].split(" ")[0]
                self.USPEX_generation_streak = line.split(" previous")[0].split(" ")[-1]

    def propagate_USPEX(
        self,
        project_dir: str,
        USPEX_check_status_script: str,
        CRYSTAL_input_directory: str,
    ) -> None:
        """Advance USPEX calculation through its states.

        Args:
            project_dir: Base project directory.
            USPEX_check_status_script: Path to status check script.
            CRYSTAL_input_directory: Path to CRYSTAL templates (for transition).
        """
        if not os.path.isdir(self.USPEX_directory):
            print(
                f"Cannot propagate USPEX calculation {self.calculation_name}, "
                f"because directory {self.USPEX_directory} does not exist."
            )
            self.status = "Stalled because USPEX directory missing"
            return

        os.chdir(self.USPEX_directory)

        output_lines = (
            subprocess.run(USPEX_check_status_script, stdout=subprocess.PIPE)
            .stdout.decode("utf-8")
            .split("\n")
        )
        status = output_lines[1].split('"')[1]

        # Verify running status with SLURM
        if status == "Running":
            running_correctly_check = (
                subprocess.run(
                    f"squeue -j {self.USPEX_SLURM_job_ID} | wc -l",
                    check=True,
                    shell=True,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")[0]
                == "2"
            )
            if not running_correctly_check:
                status = "Halted"

        if status == "Running":
            self.USPEX_status = status
            self.parse_USPEX_status_check(output_lines)
        elif status == "DONE":
            self.USPEX_status = status
            self.USPEX_done = True
            self.USPEX_SLURM_job_ID = ""
            best_structure_path = save_best_USPEX_structure(self.USPEX_directory + "/results1/")
            self.USPEX_best_structure = best_structure_path
            self.setup_CRYSTAL(project_dir, best_structure_path, CRYSTAL_input_directory)
        elif status == "Waiting":
            # Don't resubmit if job is queued
            if self.USPEX_status == "Submitted":
                running_correctly_check = (
                    subprocess.run(
                        f"squeue -j {self.USPEX_SLURM_job_ID} | wc -l",
                        check=True,
                        shell=True,
                        stdout=subprocess.PIPE,
                    ).stdout.decode("utf-8")[0]
                    == "2"
                )
            if not (self.USPEX_status == "Submitted" and running_correctly_check):
                self.activate_USPEX_daemon()
                print(
                    f"Submitted USPEX calculation {self.calculation_name} "
                    f"for the first time with job id {self.USPEX_SLURM_job_ID} "
                    f"at {get_time()}."
                )
                self.USPEX_status = "Submitted"
                self.USPEX_started = True
                self.new_USPEX_started = True
        elif status == "Halted":
            running_correctly_check = (
                subprocess.run(
                    f"squeue -j {self.USPEX_SLURM_job_ID} | wc -l",
                    check=True,
                    shell=True,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")[0]
                == "2"
            )
            if not (self.USPEX_status == "Submitted" and running_correctly_check):
                self.activate_USPEX_daemon()
                print(
                    f"Resubmitted USPEX calculation {self.calculation_name} "
                    f"with job id {self.USPEX_SLURM_job_ID} at {get_time()}."
                )
                self.USPEX_status = "Submitted"
                self.parse_USPEX_status_check(output_lines)
        elif status == "Not_A_Calculation":
            self.USPEX_status = status
        elif status in ("Multiple_Results", "Stalled"):
            self.USPEX_status = status
            self.USPEX_SLURM_job_ID = ""
            self.stalled_in_USPEX = True
            (
                self.USPEX_max_percent_done,
                self.USPEX_min_jobs_remaining,
                self.USPEX_current_generation,
                self.USPEX_generation_streak,
            ) = ("?", "?", "?", "?")
        else:
            self.USPEX_status = "UNKNOWN"

        if self.USPEX_status != "DONE":
            self.status = f"USPEX({self.USPEX_status})"
        self.USPEX_update_timestamp = get_file_timestamp(self.USPEX_directory)
        self.USPEX_status_update_timestamp = get_time()

    def activate_USPEX_daemon(self) -> None:
        """Submit USPEX job to SLURM scheduler."""
        submission_output = subprocess.run(
            "sbatch USPEX_submission.slurm",
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        self.USPEX_SLURM_job_ID = int(re.findall(r"\d+", submission_output)[0])

    def setup_CRYSTAL(
        self,
        project_dir: str,
        reference_geom_path: str,
        CRYSTAL_input_directory: str,
    ) -> None:
        """Initialize CRYSTAL calculation directory.

        Args:
            project_dir: Base project directory.
            reference_geom_path: Path to input structure (from USPEX).
            CRYSTAL_input_directory: Path to CRYSTAL input templates.
        """
        CRYSTAL_directory = f"{project_dir}/CRYSTAL/{self.calculation_name}"
        os.makedirs(CRYSTAL_directory, exist_ok=True)
        self.CRYSTAL_directory = CRYSTAL_directory

        # Copy reference geometry
        os.system(f"cp {reference_geom_path} {self.CRYSTAL_directory}/reference_geometry.cif")

        CRYSTAL_step_status_dictionary: Dict[str, str] = {}
        CRYSTAL_step_directory_dictionary: Dict[str, str] = {}

        for d in os.scandir(CRYSTAL_input_directory):
            if d.is_dir():
                d_name, d_path = d.name, d.path
                step_number = re.findall(r"\d+$", d_name.split("_")[0])
                if not len(step_number):
                    continue
                step_number = step_number[0]
                # step_name = "_".join(d_name.split("_")[1:])
                CRYSTAL_step_status_dictionary[step_number] = "Not_Started"
                new_step_folder = f"{self.CRYSTAL_directory}/{d_name}"
                CRYSTAL_step_directory_dictionary[step_number] = new_step_folder

                if step_number == "1":
                    self.CRYSTAL_current_step_directory = new_step_folder
                os.makedirs(new_step_folder, exist_ok=True)
                os.system(f"cp {d_path}/template_* {new_step_folder}/")

        self.CRYSTAL_step_status_dictionary = CRYSTAL_step_status_dictionary
        self.CRYSTAL_step_directory_dictionary = CRYSTAL_step_directory_dictionary
        self.CRYSTAL_current_step = "1"

        self.CRYSTAL_status = self.format_CRYSTAL_status()
        self.status = f"CRYSTAL({self.CRYSTAL_status})"
        self.CRYSTAL_update_timestamp = get_file_timestamp(self.CRYSTAL_current_step_directory)
        print(
            f"CRYSTAL calculation directory {self.calculation_name} "
            f"created at {self.CRYSTAL_update_timestamp}"
        )
        self.CRYSTAL_status_update_timestamp = get_time()

    def setup_CRYSTAL_step(self, CRYSTAL_input_directory: str) -> None:
        """Initialize a single CRYSTAL calculation step.

        Args:
            CRYSTAL_input_directory: Path to CRYSTAL input templates.
        """
        instantiate_script_path = (
            f"{CRYSTAL_input_directory}/instantiate_Step{self.CRYSTAL_current_step}.sh"
        )
        print(f"instantiating with {instantiate_script_path}")
        instantiate_return_code = os.system(
            f"{instantiate_script_path} {self.calculation_name} "
            f"{self.CRYSTAL_current_step_directory}"
        )
        if instantiate_return_code == 0:
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = "Waiting"
        else:
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = "Stalled"

        self.CRYSTAL_status = self.format_CRYSTAL_status()
        self.status = f"CRYSTAL({self.CRYSTAL_status})"
        self.CRYSTAL_update_timestamp = get_file_timestamp(self.CRYSTAL_current_step_directory)
        print(
            f"CRYSTAL calculation directory {self.calculation_name} "
            f"created at {self.CRYSTAL_update_timestamp}"
        )
        self.CRYSTAL_status_update_timestamp = get_time()

    def propagate_CRYSTAL_step(
        self,
        CRYSTAL_input_directory: str,
        CRYSTAL_check_status_script: str,
    ) -> None:
        """Advance a single CRYSTAL step through its states.

        Args:
            CRYSTAL_input_directory: Path to CRYSTAL input templates.
            CRYSTAL_check_status_script: Path to status check script.
        """
        initial_step_status = self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step]

        if not os.path.isdir(self.CRYSTAL_current_step_directory):
            print(
                f"Cannot propagate CRYSTAL calculation {self.calculation_name}, "
                f"because directory {self.CRYSTAL_current_step_directory} "
                "does not exist."
            )
            self.status = "Stalled because CRYSTAL directory missing"
            return

        os.chdir(self.CRYSTAL_current_step_directory)

        # Use step-specific check script if available
        check_status_script = (
            f"{CRYSTAL_input_directory}/check_status_Step{self.CRYSTAL_current_step}.sh"
        )
        if not os.path.isfile(check_status_script):
            check_status_script = CRYSTAL_check_status_script

        print(f"About to run {check_status_script}")
        output_lines = (
            subprocess.run(check_status_script, stdout=subprocess.PIPE)
            .stdout.decode("utf-8")
            .split("\n")
        )
        print(output_lines)
        status = output_lines[0].split()[1]
        print(f"Just ran {check_status_script}")

        # Verify running status with SLURM
        if status == "Running":
            running_correctly_check = (
                subprocess.run(
                    f"squeue -j {self.CRYSTAL_SLURM_job_ID} | wc -l",
                    check=True,
                    shell=True,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")[0]
                == "2"
            )
            if not running_correctly_check:
                status = "Halted"

        if status == "Running":
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = status
        elif status == "DONE":
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = status
        elif status == "Waiting":
            if initial_step_status == "Submitted":
                running_correctly_check = (
                    subprocess.run(
                        f"squeue -j {self.CRYSTAL_SLURM_job_ID} | wc -l",
                        check=True,
                        shell=True,
                        stdout=subprocess.PIPE,
                    ).stdout.decode("utf-8")[0]
                    == "2"
                )
            if not (initial_step_status == "Submitted" and running_correctly_check):
                submission_output = subprocess.run(
                    f"sbatch {self.calculation_name}.slurm",
                    check=True,
                    shell=True,
                    stdout=subprocess.PIPE,
                ).stdout.decode("utf-8")
                self.CRYSTAL_SLURM_job_ID = int(re.findall(r"\d+", submission_output)[0])
                print(
                    f"Submitted Step {self.CRYSTAL_current_step} of CRYSTAL "
                    f"calculation {self.calculation_name} for the first time "
                    f"with job id {self.CRYSTAL_SLURM_job_ID} at {get_time()}."
                )
                self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = "Submitted"
                self.CRYSTAL_started = True
                self.new_CRYSTAL_started = True
        elif status in ("Files_Missing", "Timed_Out", "Nonexistant", "Stalled"):
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = status
            self.CRYSTAL_SLURM_job_ID = ""
            self.stalled_in_CRYSTAL = True
        else:
            self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] = "UNKNOWN"

        self.CRYSTAL_status = self.format_CRYSTAL_status()
        self.status = f"CRYSTAL({self.CRYSTAL_status})"
        self.CRYSTAL_update_timestamp = get_file_timestamp(self.CRYSTAL_current_step_directory)
        self.CRYSTAL_status_update_timestamp = get_time()

    def propagate_CRYSTAL(
        self,
        CRYSTAL_input_directory: str,
        CRYSTAL_check_status_script: str,
    ) -> None:
        """Advance CRYSTAL calculation through all steps.

        Args:
            CRYSTAL_input_directory: Path to CRYSTAL input templates.
            CRYSTAL_check_status_script: Path to status check script.
        """
        print(self.CRYSTAL_current_step, type(self.CRYSTAL_current_step))
        for key, value in self.CRYSTAL_step_status_dictionary.items():
            print(key, type(key), value, type(value))

        if self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] == "Not_Started":
            self.setup_CRYSTAL_step(CRYSTAL_input_directory)
        elif self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step] == "DONE":
            possibly_new_step = str(int(self.CRYSTAL_current_step) + 1)
            if possibly_new_step in self.CRYSTAL_step_status_dictionary.keys():
                self.CRYSTAL_current_step = possibly_new_step
                self.CRYSTAL_current_step_directory = self.CRYSTAL_step_directory_dictionary[
                    possibly_new_step
                ]
                self.setup_CRYSTAL_step(CRYSTAL_input_directory)
            elif all(status == "DONE" for status in self.CRYSTAL_step_status_dictionary.values()):
                self.CRYSTAL_status = "DONE"
                self.status = "DONE"
                self.CRYSTAL_update_timestamp = get_file_timestamp(
                    self.CRYSTAL_current_step_directory
                )
                self.CRYSTAL_status_update_timestamp = get_time()
            else:
                self.stalled_in_CRYSTAL = True
                self.CRYSTAL_status = "Stalled"
                self.status = "Stalled because CRYSTAL directory missing"
                self.CRYSTAL_update_timestamp = get_file_timestamp(
                    self.CRYSTAL_current_step_directory
                )
                self.CRYSTAL_status_update_timestamp = get_time()
        else:
            no_new_changes = self.CRYSTAL_update_timestamp == get_file_timestamp(
                self.CRYSTAL_current_step_directory
            )
            if hasattr(self, "stalled_in_CRYSTAL") and self.stalled_in_CRYSTAL and no_new_changes:
                self.CRYSTAL_status_update_timestamp = get_time()
            else:
                self.propagate_CRYSTAL_step(CRYSTAL_input_directory, CRYSTAL_check_status_script)

    def format_CRYSTAL_status(self) -> str:
        """Format current CRYSTAL status for display.

        Returns:
            String like "1_Waiting" or "2_Running".
        """
        return (
            f"{self.CRYSTAL_current_step}_"
            f"{self.CRYSTAL_step_status_dictionary[self.CRYSTAL_current_step]}"
        )

    def save_row(self, pd_series: pd.Series) -> None:
        """Save current state back to inventory row.

        Args:
            pd_series: Row to update (modified in place).
        """
        self.row_last_updated = get_time()
        print(f"Finished updating {self.calculation_name} at {self.row_last_updated}")

        for key, value in pd_series.items():
            if hasattr(self, key):
                if "dictionary" in key:
                    value = dict_to_str(getattr(self, key))
                else:
                    value = getattr(self, key)
                pd_series[key] = value
