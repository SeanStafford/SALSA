"""
SALSA - Substitution, Approximation, evoLutionary Search, and Ab-initio

A high-throughput computational materials discovery pipeline for identifying
materials with target properties.

The workflow combines:
- Ionic substitution from known compounds (ICSD database)
- Property interpolation for candidate filtering
- USPEX evolutionary crystal structure prediction
- CRYSTAL DFT calculations for electronic properties
"""

__version__ = "0.1.0"

from salsa.core.propagate import InventoryRow
from salsa.crystal.extract_bandgap import get_bandgap
from salsa.crystal.instantiate_d12 import instantiate_D12

__all__ = ["InventoryRow", "instantiate_D12", "get_bandgap"]
