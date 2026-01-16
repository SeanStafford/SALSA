# salsa/core

Workflow orchestration and state management.

## Modules

### propagate.py

The `InventoryRow` class implements a state machine for managing compounds through the SALSA pipeline:

```
new_candidate → USPEX(Waiting) → USPEX(Submitted) → USPEX(Running) → USPEX(DONE)
    → CRYSTAL(1_Waiting) → CRYSTAL(1_Submitted) → ... → CRYSTAL(N_DONE) → DONE
```

Each compound's state is tracked in a CSV inventory with columns for:
- Composition and source information
- Interpolated properties and parent compounds
- USPEX calculation status and directory paths
- CRYSTAL calculation steps and results

## Usage

```python
from salsa.core import InventoryRow

# Load or create a compound row
row = InventoryRow(inventory_path="inventory.csv", compound_name="PbCuSeCl")

# Advance through workflow states
row.submit_uspex()
row.check_uspex_status()
row.submit_crystal(step=1)
```
