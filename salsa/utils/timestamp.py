"""Timestamp utilities for SALSA pipeline."""

import datetime
import os

TIMESTAMP_FORMAT = "%H:%M:%S %Y-%m-%d"


def get_time() -> str:
    """Get current timestamp as formatted string.

    Returns:
        Current time formatted as HH:MM:SS YYYY-MM-DD.
    """
    return datetime.datetime.now().strftime(TIMESTAMP_FORMAT)


def get_file_timestamp(path: str) -> str:
    """Get file modification timestamp as formatted string.

    Args:
        path: Path to file.

    Returns:
        File modification time formatted as HH:MM:SS YYYY-MM-DD.
    """
    int_timestamp = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(int_timestamp).strftime(TIMESTAMP_FORMAT)
