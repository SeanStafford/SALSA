"""Collection utilities for SALSA pipeline."""

import collections.abc
from typing import Any, Generator, List


def flatten_to_generator(nested_list: Any) -> Generator:
    """Recursively flatten nested iterables into a generator.

    Useful for iterables of different shapes and types.
    From stackoverflow.com/a/2158532

    Args:
        nested_list: Arbitrarily nested iterable structure.

    Yields:
        Individual non-iterable elements from the nested structure.
    """
    for element in nested_list:
        if isinstance(element, collections.abc.Iterable) and not isinstance(element, (str, bytes)):
            yield from flatten_to_generator(element)
        else:
            yield element


def flatten_to_list(*nested_list: Any) -> List:
    """Recursively flatten nested iterables into a list.

    Args:
        *nested_list: Arbitrarily nested iterable structures.

    Returns:
        Flattened list of all elements.
    """
    return list(flatten_to_generator(nested_list))
