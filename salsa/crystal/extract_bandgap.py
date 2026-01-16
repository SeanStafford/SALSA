"""Extract bandgap information from CRYSTAL output files.

This module parses CRYSTAL quantum chemistry output to determine
electronic band structure properties.

Adapted from code by Danny and Marcus.
"""

from typing import List, Tuple, Union

# Hartree to eV conversion factor
HARTREE_TO_EV = 27.2114


def get_bandgap(
    output_content: List[str],
    return_type: bool = True,
    verbose: bool = False,
) -> Union[float, Tuple[float, str]]:
    """Determine bandgap in eV and optionally the bandgap type.

    Parses CRYSTAL output to extract conduction band minimum (CBM) and
    valence band maximum (VBM), handling both spin-polarized (alpha/beta)
    and non-spin-polarized calculations.

    Args:
        output_content: Lines from CRYSTAL output file.
        return_type: If True, return tuple of (bandgap, type).
        verbose: If True, print debug information.

    Returns:
        If return_type is True: (bandgap_eV, bandgap_type) where type is
            "Direct", "Indirect", or "None" (conducting).
        If return_type is False: bandgap_eV only.

    Example:
        >>> with open("crystal.out", "r") as f:
        ...     content = f.readlines()
        >>> bandgap, gap_type = get_bandgap(content)
        >>> print(f"Bandgap: {bandgap:.3f} eV ({gap_type})")
    """
    # Initialize indices for keyword search
    index_alpha = 0
    index_beta = 0
    index_direct = 0
    index_cond = 0
    index_indirect = 0
    alpha_cond_band: List[str] = []
    alpha_val_band: List[str] = []
    beta_cond_band: List[str] = []
    beta_val_band: List[str] = []
    bandgap_type = "Undetermined"

    # Find relevant keyword positions
    for line in output_content:
        if "ALPHA      ELECTRONS" in line:
            index_alpha = output_content.index(line)
        if "BETA       ELECTRONS" in line:
            index_beta = output_content.index(line)
        if line.startswith(" DIRECT ENERGY BAND GAP"):
            index_direct = output_content.index(line)
        if "POSSIBLY CONDUCTING STATE" in line:
            index_cond = output_content.index(line)
        if "INDIRECT ENERGY BAND GAP" in line:
            index_indirect = output_content.index(line)

    if verbose:
        print(f"alpha line #: {index_alpha}")
        print(f"beta line #: {index_beta}")
        print(f"direct line #: {index_direct}")
        print(f"cond line #: {index_cond}")
        print(f"indirect line #: {index_indirect}")

    # Direct bandgap is last keyword found
    if (
        index_direct > index_alpha
        and index_direct > index_beta
        and index_direct > index_cond
        and index_direct > index_indirect
    ):
        for index in range(index_direct - 4, index_direct + 1):
            if "TOP OF VALENCE" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_val_band.append(unclean_alpha[10].split(";")[0])
            if "BOTTOM OF VIRTUAL" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_cond_band.append(unclean_alpha[10].split(";")[0])
        beta_cond_band = alpha_cond_band
        beta_val_band = alpha_val_band
        bandgap_type = "Direct"

    # Conducting state is last keyword found
    elif (
        index_cond > index_alpha
        and index_cond > index_beta
        and index_cond > index_direct
        and index_cond > index_indirect
    ):
        unclean_alpha = [x for x in output_content[index_cond].split(" ") if x != ""]
        alpha_val_band.append(unclean_alpha[5].split(";")[0])
        alpha_cond_band = alpha_val_band
        beta_cond_band = alpha_cond_band
        beta_val_band = alpha_val_band
        bandgap_type = "None"

    # Alpha/beta spin-polarized is last keyword found
    elif index_alpha > index_cond and index_alpha > index_direct and index_alpha > index_indirect:
        for index in range(index_alpha + 2, index_alpha + 7):
            if "TOP OF VALENCE" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_val_band.append(unclean_alpha[10].split(";")[0])
            if "BOTTOM OF VIRTUAL" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_cond_band.append(unclean_alpha[10].split(";")[0])
        for index in range(index_beta + 2, index_beta + 7):
            if "TOP OF VALENCE" in output_content[index]:
                unclean_beta = [x for x in output_content[index].split(" ") if x != ""]
                beta_val_band.append(unclean_beta[10].split(";")[0])
            if "BOTTOM OF VIRTUAL" in output_content[index]:
                unclean_beta = [x for x in output_content[index].split(" ") if x != ""]
                beta_cond_band.append(unclean_beta[10].split(";")[0])

    # Indirect bandgap is last keyword found
    elif (
        index_indirect > index_direct
        and index_indirect > index_cond
        and index_indirect > index_alpha
    ):
        for index in range(index_indirect - 4, index_indirect + 1):
            if "TOP OF VALENCE" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_val_band.append(unclean_alpha[10].split(";")[0])
            if "BOTTOM OF VIRTUAL" in output_content[index]:
                unclean_alpha = [x for x in output_content[index].split(" ") if x != ""]
                alpha_cond_band.append(unclean_alpha[10].split(";")[0])
        beta_cond_band = alpha_cond_band
        beta_val_band = alpha_val_band
        bandgap_type = "Indirect"
    else:
        print("error, no keyword")

    # Find minimum conduction and maximum valence across spins
    min_alpha_c = alpha_cond_band[0]
    max_alpha_v = alpha_val_band[0]
    min_beta_c = beta_cond_band[0]
    max_beta_v = beta_val_band[0]

    if len(alpha_cond_band) > 1:
        for shell in alpha_cond_band:
            if float(shell) < float(alpha_cond_band[0]):
                min_alpha_c = shell

    if len(alpha_val_band) > 1:
        for shell in alpha_val_band:
            if float(shell) > float(alpha_val_band[0]):
                max_alpha_v = shell

    if len(beta_cond_band) > 1:
        for shell in beta_cond_band:
            if float(shell) < float(beta_cond_band[0]):
                min_beta_c = shell

    if len(beta_val_band) > 1:
        for shell in beta_val_band:
            if float(shell) < float(beta_val_band[0]):
                max_beta_v = shell

    min_c = min_beta_c if float(min_alpha_c) > float(min_beta_c) else min_alpha_c
    max_v = max_alpha_v if float(max_alpha_v) > float(max_beta_v) else max_beta_v

    conduction_min = float(min_c) * HARTREE_TO_EV
    valence_max = float(max_v) * HARTREE_TO_EV

    if return_type:
        return conduction_min - valence_max, bandgap_type
    else:
        return conduction_min - valence_max
