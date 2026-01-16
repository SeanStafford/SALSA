"""Generate CRYSTAL D12 input files from CIF structures.

This module converts crystallographic structure files (CIF format) into
CRYSTAL quantum chemistry input files (D12 format), handling:
- Space group and lattice parameter extraction
- Basis set compilation with ECP support
- Automatic k-point grid determination

The primary function was inspired by and adapted from CIF2D12 function
written by Danny and Marcus.
"""

import math
import os
import re
from typing import List, Optional, Tuple

import ase.spacegroup as spacegroup
import numpy as np
from ase.io import read

# Template keywords for D12 file generation
D12_TEMPLATE_KEYWORDS = {
    "Title": "CALCULATION_NAME",
    "Reference Geometry": "GEOMETRY_INPUT_BLOCK",
    "Geometry Editing": "GEOMETRY_OPTIMIZATION_BLOCK",
    "Basis Set": "BASIS_SET_BLOCK",
    "k-Points": "K_POINTS_BLOCK",
}


def extract_BULK_reference_geometry_with_sym(
    structure,
    input_file: str = "",
    ECPs: Tuple[int, ...] = (),
) -> str:
    """Extract reference geometry with symmetry for CRYSTAL BULK calculation.

    Args:
        structure: ASE Atoms object containing the crystal structure.
        input_file: Source file path (for error messages).
        ECPs: Tuple of atomic numbers using effective core potentials.

    Returns:
        Formatted string containing space group, lattice parameters,
        and atomic positions for CRYSTAL input.
    """
    reference_geometry_text = ""

    # Get space group
    if "spacegroup" in structure.info:
        sg = structure.info["spacegroup"].no
    else:
        no_sg_warning = "Warning: When extracting reference geometry "
        if input_file:
            no_sg_warning += f"from {input_file} "
        no_sg_warning += "could not identify spacegroup so 'P 1' will be used."
        print(no_sg_warning)
        sg = 1
    reference_geometry_text += str(sg) + "\n"

    # Get lattice parameters
    cells_params = structure.cell.get_bravais_lattice().vars()
    min_params_printout = " ".join([f"{param:.6f}   " for param in cells_params.values()])
    reference_geometry_text += min_params_printout + "\n"

    # Get atom positions
    pos = spacegroup.get_basis(structure)
    n_atoms = len(pos)
    reference_geometry_text += str(n_atoms) + "\n"

    atomic_symbols = structure.get_chemical_symbols()
    atomic_nums = structure.get_atomic_numbers()
    # Add 200 to atomic number if using ECP
    atomic_nums = [a_n + 200 * int(a_n in ECPs) for a_n in atomic_nums]
    reference_geometry_text += "\n".join(
        [
            f"{atomic_nums[i]:<3d} {pos[i][0]:10.6f}  {pos[i][1]:10.6f}  {pos[i][2]:10.6f} # {atomic_symbols[i]:<2s}"
            for i in range(n_atoms)
        ]
    )
    return reference_geometry_text


def compile_basis_set(
    structure,
    basis_set_directory: str,
    input_file: str = "",
) -> Optional[Tuple[str, List[int]]]:
    """Compile basis set block from individual element files.

    Args:
        structure: ASE Atoms object containing the crystal structure.
        basis_set_directory: Path to directory containing basis set files.
        input_file: Source file path (for error messages).

    Returns:
        Tuple of (basis_set_text, ECP_atomic_nums) or None if error.
        ECP_atomic_nums lists atomic numbers using effective core potentials.
    """
    basis_set_text = ""
    atomic_nums = np.unique(structure.get_atomic_numbers())
    ECP_atomic_nums: List[int] = []

    for atomic_num in atomic_nums:
        basis_set_file_matches = []
        for basis_set_file in os.listdir(basis_set_directory):
            basis_set_path = basis_set_directory + "/" + basis_set_file
            file_atomic_nums = re.findall(r"\d+", basis_set_file)
            if str(atomic_num) in file_atomic_nums:
                if len(file_atomic_nums) > 1:
                    unparsable_error = f"Basis set file {basis_set_path} cannot be parsed. "
                    if input_file:
                        unparsable_error += f"Cannot convert {input_file} "
                    unparsable_error += "to d12."
                    print(unparsable_error)
                    return None
                else:
                    basis_set_file_matches.append(basis_set_path)

        if len(basis_set_file_matches) == 1:
            with open(basis_set_file_matches[0], "r") as file:
                lines = file.readlines()
            basis_set_text += "".join(lines)
            atomic_identifier = int(lines[0].split()[0])
            if atomic_identifier > 200:
                ECP_atomic_nums.append(atomic_identifier - 200)
        elif len(basis_set_file_matches) == 0:
            missing_error = (
                f"Basis set for element {atomic_num} is missing from '{basis_set_directory}'. "
            )
            if input_file:
                missing_error += f"Cannot convert {input_file} "
            missing_error += "to d12."
            print(missing_error)
            return None
        else:
            multiple_error = (
                f"Multiple basis set files {basis_set_file_matches} "
                f"exist for element {atomic_num}. "
            )
            if input_file:
                multiple_error += f"Cannot convert {input_file} "
            multiple_error += "to d12."
            print(multiple_error)
            return None

    basis_set_text += "99 0\nEND"
    return basis_set_text, ECP_atomic_nums


def determine_k_point_grid(structure, k_point_criterion: float) -> str:
    """Determine Monkhorst-Pack k-point grid based on lattice constants.

    The number of k-points along each direction is chosen such that
    k_points * lattice_constant >= k_point_criterion.

    Args:
        structure: ASE Atoms object containing the crystal structure.
        k_point_criterion: Minimum product of k-points and lattice constant.

    Returns:
        Formatted SHRINK block for CRYSTAL input.
    """
    a, b, c = structure.cell.cellpar()[:3]

    ka = math.ceil(k_point_criterion / a)
    kb = math.ceil(k_point_criterion / b)
    kc = math.ceil(k_point_criterion / c)
    k_ISP = 2 * max(ka, kb, kc)

    shrink_text = "SHRINK\n"
    shrink_text += f"{0:2d} {k_ISP:2d}\n"
    shrink_text += f"{ka:2d} {kb:2d} {kc:2d}"

    return shrink_text


def instantiate_D12(
    input_geometry_file: str,
    output_D12: str,
    template_D12: str,
    calculation_name: str,
    basis_set_directory: str,
    D12_type: str = "BULK",
    k_point_criterion: float = 40,
) -> None:
    """Generate CRYSTAL D12 input file from CIF structure.

    Args:
        input_geometry_file: Path to input CIF file.
        output_D12: Path for output D12 file.
        template_D12: Path to D12 template file.
        calculation_name: Name for the calculation (used in title).
        basis_set_directory: Path to directory containing basis set files.
        D12_type: Type of calculation ("BULK" or "SLAB").
        k_point_criterion: Minimum k-point * lattice constant product.

    Note:
        SLAB calculations are not yet implemented. See helpscripts/code/
        create_d12_from_cif.py in the mendozacortesgroup GitHub for SLAB support.
    """
    if D12_type not in ["BULK", "SLAB"]:
        print(f"Warning: Do not recognize D12 type input '{D12_type}'. Using 'BULK' by default.")
        D12_type = "BULK"
    elif D12_type == "SLAB":
        slab_warning = (
            "Warning: You requested a 'SLAB' D12, but this function is not "
            "implemented for that.\n"
            "See helpscripts/code/create_d12_from_cif.py in the mendozacortesgroup "
            "GitHub for SLAB support.\n"
            f"Cannot convert {input_geometry_file} to d12."
        )
        print(slab_warning)
        return

    structure = read(input_geometry_file)

    with open(template_D12, "r") as file:
        D12_lines = file.readlines()

    # Compile basis set first to identify ECPs
    ECPs: Tuple[int, ...] = ()
    for i in range(len(D12_lines)):
        if D12_TEMPLATE_KEYWORDS["Title"] in D12_lines[i]:
            D12_lines[i] = D12_lines[i].replace(D12_TEMPLATE_KEYWORDS["Title"], calculation_name)
        if D12_TEMPLATE_KEYWORDS["Basis Set"] in D12_lines[i]:
            result = compile_basis_set(
                structure, basis_set_directory, input_file=input_geometry_file
            )
            if result is None:
                return
            basis_set_text, ECP_list = result
            ECPs = tuple(ECP_list)
            D12_lines[i] = D12_lines[i].replace(D12_TEMPLATE_KEYWORDS["Basis Set"], basis_set_text)

    # Insert reference geometry after basis sets (need ECP info)
    for i in range(len(D12_lines)):
        if D12_TEMPLATE_KEYWORDS["Reference Geometry"] in D12_lines[i]:
            reference_geometry_text = extract_BULK_reference_geometry_with_sym(
                structure, input_file=input_geometry_file, ECPs=ECPs
            )
            D12_lines[i] = D12_lines[i].replace(
                D12_TEMPLATE_KEYWORDS["Reference Geometry"], reference_geometry_text
            )
        if D12_TEMPLATE_KEYWORDS["k-Points"] in D12_lines[i]:
            k_points_text = determine_k_point_grid(structure, k_point_criterion)
            D12_lines[i] = D12_lines[i].replace(D12_TEMPLATE_KEYWORDS["k-Points"], k_points_text)

    with open(output_D12, "w") as file:
        for line in D12_lines:
            file.write(line)
