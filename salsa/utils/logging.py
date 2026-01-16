"""Logging utilities for SALSA pipeline."""

import sys
from typing import TextIO


class Logger:
    """Dual-output logger that writes to both terminal and file.

    This logger captures both stdout and stderr, writing all output to
    a log file while preserving terminal display.

    Adapted from stackoverflow.com/a/41477104

    Attributes:
        terminal: Original stdout stream.
        error: Original stderr stream.
        logfile: Open file handle for logging.

    Example:
        >>> logger = Logger("calculation.log")
        >>> print("This goes to terminal and file")
        >>> logger.stop()  # Restore original streams
    """

    def __init__(self, filename: str):
        """Initialize logger with output file.

        Args:
            filename: Path to log file (will be opened in append mode).
        """
        self.terminal: TextIO = sys.stdout
        self.error: TextIO = sys.stderr
        self.logfile: TextIO = open(filename, "a")
        sys.stdout = self
        sys.stderr = self

    def write(self, message: str, logfile_only: bool = False) -> None:
        """Write message to terminal and/or log file.

        Args:
            message: Text to write.
            logfile_only: If True, skip terminal output.
        """
        if not logfile_only:
            self.terminal.write(message)
        self.logfile.write(message)

    def flush(self) -> None:
        """Flush output streams (required for file-like interface)."""
        self.terminal.flush()
        self.logfile.flush()

    def stop(self) -> None:
        """Close log file and restore original stdout/stderr."""
        self.logfile.close()
        sys.stdout = self.terminal
        sys.stderr = self.error
