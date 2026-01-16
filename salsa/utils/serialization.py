"""Serialization utilities for SALSA pipeline."""

import base64
import os
from typing import Dict


def generate_unique_id(length: int = 5) -> str:
    """Generate a unique base64-encoded identifier.

    Args:
        length: Length of the returned ID string.

    Returns:
        A URL-safe unique identifier string.
    """
    return base64.b64encode(os.urandom(64)).decode().replace("/", "").replace("+", "")[:length]


def str_to_dict(dict_string: str, value_type: str = "int") -> Dict:
    """Parse a serialized dictionary string.

    Args:
        dict_string: String in format "key1:value1::key2:value2::key3:value3"
        value_type: Type to cast values to ("int" or "str").

    Returns:
        Reconstructed dictionary.
    """
    new_list = dict_string.split("::")
    new_dict = {}
    for pair in new_list:
        key, value = pair.split(":")
        if value_type == "int":
            value = int(value)
        new_dict[key] = value
    return new_dict


def dict_to_str(a_dict: Dict) -> str:
    """Serialize a dictionary to string format.

    Args:
        a_dict: Dictionary to serialize.

    Returns:
        String in format "key1:value1::key2:value2::key3:value3"
    """
    dict_string = ""
    for key, value in a_dict.items():
        dict_string += "{}:{}::".format(key, value)
    return dict_string[:-2]
