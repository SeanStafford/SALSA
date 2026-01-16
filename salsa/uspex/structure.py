"""USPEX structure handling utilities."""


def save_best_USPEX_structure(results_dir: str) -> str:
    """Extract the best structure from USPEX results.

    Reads the BESTIndividuals file to identify the lowest-energy structure,
    then extracts it from the symmetrized_structures.cif file.

    Args:
        results_dir: Path to USPEX results directory (e.g., "results1/").

    Returns:
        Path to the extracted best structure CIF file.
    """
    symmetrized_cifs = results_dir + "/symmetrized_structures.cif"
    best_individuals = results_dir + "/BESTIndividuals"
    best_only = results_dir + "/best_symmetrized_structure.cif"

    with open(best_individuals, "r") as f:
        best_individual_index = f.readlines()[-1].split()[1]
    print("best_individual_index is {}".format(best_individual_index))

    saved_lines = []
    special_index = str(best_individual_index)
    with open(symmetrized_cifs, "r") as f:
        save_line = False
        for line in f.readlines():
            if "data_findsym-STRUC" in line:
                if special_index in line:
                    save_line = True
                else:
                    save_line = False
            if save_line:
                saved_lines.append(line)

    with open(best_only, "w") as f:
        for line in saved_lines:
            f.write(line)

    return best_only
