# salsa/uspex

Interface for USPEX evolutionary crystal structure prediction.

## Modules

### structure.py

Utilities for handling USPEX output structures.

**Key function:** `save_best_USPEX_structure(results_dir)`

Extracts the lowest-energy structure from a completed USPEX run:
1. Reads `BESTIndividuals` to identify the best structure index
2. Extracts that structure from `symmetrized_structures.cif`
3. Saves to `best_symmetrized_structure.cif`

## External Dependency

USPEX must be installed separately on the HPC system. See [uspex-team.org](https://uspex-team.org/).

USPEX interfaces with VASP for energy evaluation during structure prediction, requiring:
- VASP installation and license
- POTCAR pseudopotential files (see `reference/potcars/`)
