import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class CliResult(Generic[T]):
    """Result wrapper for CLI operations with error handling."""

    value: T | None
    code: int

    def is_error(self) -> bool:
        """Check if this result represents an error."""
        return self.code != 0

    def unwrap(self) -> T:
        """Get the value, asserting it's not None. Use after checking is_error()."""
        assert self.value is not None, "Cannot unwrap an error result"
        return self.value


def get_root_dir() -> Path:
    """Get the root directory of the project (parent of src/)."""
    return Path(__file__).parent.parent


def read_file_utf8(file_path: Path) -> str:
    """Read a file with UTF-8 encoding."""
    return file_path.read_text(encoding="utf-8")


def write_file_utf8(file_path: Path, content: str) -> None:
    """Write a file with UTF-8 encoding."""
    file_path.write_text(content, encoding="utf-8")


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)
