# salsa/crystal

Interface for CRYSTAL quantum chemistry calculations.

## Modules

### instantiate_d12.py

Converts CIF crystal structures to CRYSTAL D12 input format.

**Key function:** `instantiate_D12(cif_path, template_path, basis_set_dir, ...)`

Handles:
- Space group and lattice parameter extraction via ASE
- Basis set compilation with automatic ECP (effective core potential) detection
- K-point grid determination based on lattice constants
- Template-based D12 file generation

### extract_bandgap.py

Parses CRYSTAL output files to extract electronic band structure properties.

**Key function:** `get_bandgap(output_content, return_type=True)`

Returns:
- Band gap in eV
- Band gap type: "Direct", "Indirect", or "None" (conducting)

Handles both spin-polarized (alpha/beta) and non-spin-polarized calculations.
