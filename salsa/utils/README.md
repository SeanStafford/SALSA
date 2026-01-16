# salsa/utils

Shared utilities for the SALSA pipeline, organized by concern.

## Modules

### logging.py

Dual-output logger that writes to both terminal and file.

```python
from salsa.utils.logging import Logger

logger = Logger("calculation.log")
print("This goes to terminal and log file")
logger.stop()  # Restore original streams
```

### timestamp.py

Timestamp formatting utilities.

```python
from salsa.utils.timestamp import get_time, get_file_timestamp

current = get_time()           # "14:30:25 2023-12-01"
modified = get_file_timestamp("file.txt")
```

### serialization.py

Dictionary serialization for CSV storage and ID generation.

```python
from salsa.utils.serialization import str_to_dict, dict_to_str, generate_unique_id

# Serialize dict for CSV column
s = dict_to_str({"Pb": 1, "Se": 1})  # "Pb:1::Se:1"
d = str_to_dict(s)                    # {"Pb": 1, "Se": 1}

# Generate unique compound ID
uid = generate_unique_id(5)  # e.g., "xK2mQ"
```

### collections.py

Utilities for flattening nested iterables.

```python
from salsa.utils.collections import flatten_to_list

flat = flatten_to_list([[1, 2], [3, [4, 5]]])  # [1, 2, 3, 4, 5]
```
