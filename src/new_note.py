"""Create a new timestamped note from template."""

import argparse
import pathlib
import re
import secrets
import sys
from datetime import datetime

from src.core import CliResult, print_error


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for creating a new note."""
    parser = argparse.ArgumentParser(description="Create a new timestamped note")
    parser.add_argument("title", help="Title of the note")
    parser.add_argument(
        "--tags",
        default="general",
        help="Comma-separated tags (default: general)",
    )
    parser.add_argument(
        "--category",
        default="default",
        help="Note category (default: default)",
    )
    parser.add_argument(
        "--summary",
        default="Add summary here",
        help="Short description/summary",
    )
    return parser.parse_args()


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def _get_template_path(root_dir: pathlib.Path) -> CliResult[pathlib.Path]:
    """Get the note template path and verify it exists."""
    template_path = root_dir / "templates" / "note_template.md"

    if not template_path.exists():
        print_error(f"Template not found at {template_path}")
        return CliResult(None, 1)
    return CliResult(template_path, 0)


def _create_filename(date: str, title: str) -> str:
    """Generate a filename with date, slugified title, and random hash."""
    if len(slug := _slugify(title)) == 0:
        slug = "untitled-note"
    return f"{date}-{slug}-{secrets.token_hex(3)}.md"


def _create_note_path(
    root_dir: pathlib.Path, filename: str, year: str
) -> CliResult[pathlib.Path]:
    """Create the notes directory structure and validate the note path."""
    notes_dir = root_dir / "notes" / year
    try:
        notes_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print_error(f"Failed to create directory {notes_dir}: {e}")
        return CliResult(None, 1)

    note_path = notes_dir / filename
    return CliResult(note_path, 0)


def _replace_template_placeholders(
    args: argparse.Namespace, template_path: pathlib.Path, date: str, time: str
) -> CliResult[str]:
    """Read template and replace placeholders with note data."""
    try:
        template_content = template_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: Failed to read template: {e}", file=sys.stderr)
        return CliResult(None, 1)

    note_content = template_content.replace("{{TITLE}}", args.title)
    note_content = note_content.replace("{{DATE}}", date)
    note_content = note_content.replace("{{TIME}}", time)
    note_content = note_content.replace("{{TAGS}}", args.tags)
    note_content = note_content.replace("{{SHORT_DESCRIPTION}}", args.summary)
    note_content = note_content.replace("{{CATEGORY}}", args.category)
    return CliResult(note_content, 0)


def _write_note_content(
    note_path: pathlib.Path, content: str
) -> CliResult[pathlib.Path]:
    """Write note content to file using exclusive creation (prevents race conditions)."""
    try:
        with note_path.open(mode="x", encoding="utf-8") as f:
            f.write(content)
    except FileExistsError:
        print(f"Error: Note already exists at {note_path}", file=sys.stderr)
        return CliResult(None, 1)
    except OSError as e:
        print(f"Error: Failed to write note to {note_path}: {e}", file=sys.stderr)
        return CliResult(None, 1)
    return CliResult(note_path, 0)


def main() -> int:
    """Main entry point for creating a new timestamped note."""
    args = _parse_args()

    root_dir = pathlib.Path(__file__).parent.parent
    if (template_path := _get_template_path(root_dir)).is_error():
        return template_path.code

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    year = now.strftime("%Y")

    if (
        content := _replace_template_placeholders(
            args, template_path.unwrap(), date_str, time_str
        )
    ).is_error():
        return content.code

    filename = _create_filename(date_str, args.title)
    if (note_path := _create_note_path(root_dir, filename, year)).is_error():
        return note_path.code
    if (
        written_note := _write_note_content(note_path.unwrap(), content.unwrap())
    ).is_error():
        return written_note.code

    print(f"Created note: {written_note.unwrap()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
