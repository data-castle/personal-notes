"""Sync notes by updating timestamps, committing, and pushing to remote."""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from src.core import (
    CliResult,
    get_root_dir,
    print_error,
    read_file_utf8,
    write_file_utf8,
)

LAST_UPDATED_PATTERN = r"^- \*\*Last updated:\*\* \d{4}-\d{2}-\d{2} \d{2}:\d{2}$"


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for syncing notes."""
    parser = argparse.ArgumentParser(
        description="Sync notes: update timestamps, commit, and push"
    )
    parser.add_argument(
        "-m",
        "--message",
        help="Custom commit message (default: auto-generated)",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Commit but don't push to remote",
    )
    return parser.parse_args()


def _update_timestamp_in_note(file_path: Path) -> bool:
    """Update the 'Last updated' timestamp in a note file. Returns True if updated."""
    try:
        content = read_file_utf8(file_path)
        now = datetime.now()
        new_timestamp = f"- **Last updated:** {now.strftime('%Y-%m-%d %H:%M')}"

        updated_content, count = re.subn(
            LAST_UPDATED_PATTERN,
            new_timestamp,
            content,
            count=1,
            flags=re.MULTILINE,
        )

        if count > 0:
            write_file_utf8(file_path, updated_content)
            return True

        return False

    except Exception as e:
        print(
            f"Warning: Could not update timestamp in {file_path}: {e}", file=sys.stderr
        )
        return False


def _is_note_file(path_str: str) -> bool:
    """Check if a path string represents a note markdown file."""
    # Normalize path separators for cross-platform compatibility
    normalized_path = path_str.replace("\\", "/")
    return normalized_path.startswith("notes/") and normalized_path.endswith(".md")


def _add_note_if_exists(path_str: str, notes_list: list[Path], repo_root: Path) -> None:
    """Add a note file path to the list if it exists and is not already present."""
    file_path = repo_root / path_str
    if file_path.exists() and file_path not in notes_list:
        notes_list.append(file_path)


def _get_modified_notes(repo: Repo) -> list[Path]:
    """Get list of modified markdown files in notes/ directory."""
    modified_files = []
    repo_root = Path(repo.working_dir)

    # Get untracked files
    for item in repo.untracked_files:
        if _is_note_file(item):
            _add_note_if_exists(item, modified_files, repo_root)

    # Get modified files from diff (unstaged changes)
    for diff in repo.index.diff(None):
        if _is_note_file(diff.a_path):
            _add_note_if_exists(diff.a_path, modified_files, repo_root)

    # Get staged files
    for diff in repo.index.diff("HEAD"):
        if diff.a_path and _is_note_file(diff.a_path):
            _add_note_if_exists(diff.a_path, modified_files, repo_root)

    return modified_files


def _generate_commit_message(modified_files: list[Path]) -> str:
    """Generate an automatic commit message based on modified files."""
    if len(modified_files) == 0:
        return "Sync notes"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    count = len(modified_files)

    if count == 1:
        # Extract title from the single note
        try:
            content = read_file_utf8(modified_files[0])
            title_match = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
            if title_match:
                title = title_match.group(1)
                return f"Update note: {title}"
        except Exception:
            pass
        return f"Update note - {now}"

    return f"Sync {count} notes - {now}"


def _get_repository(root_dir: Path) -> CliResult[Repo]:
    """Get the git repository instance."""
    try:
        repo = Repo(root_dir)
        return CliResult(repo, 0)
    except InvalidGitRepositoryError:
        print_error("Not in a git repository")
        return CliResult(None, 1)


def _update_note_timestamps(modified_notes: list[Path]) -> int:
    """Update timestamps in modified notes. Returns count of updated notes."""
    updated_count = 0
    for note in modified_notes:
        if _update_timestamp_in_note(note):
            updated_count += 1
    return updated_count


def _stage_all_changes(repo: Repo) -> CliResult[None]:
    """Stage all changes in the repository."""
    try:
        repo.git.add(".")
        return CliResult(None, 0)
    except GitCommandError as e:
        print_error(f"Staging changes: {e}")
        return CliResult(None, 1)


def _commit_changes(repo: Repo, message: str) -> CliResult[None]:
    """Commit staged changes with the given message."""
    try:
        repo.index.commit(message)
        return CliResult(None, 0)
    except GitCommandError as e:
        print_error(f"Committing changes: {e}")
        return CliResult(None, 1)


def _push_to_remote(repo: Repo) -> CliResult[None]:
    """Push commits to the remote origin."""
    try:
        origin = repo.remote(name="origin")
        origin.push()
        return CliResult(None, 0)
    except GitCommandError as e:
        print_error(f"Pushing to remote: {e}")
        print("Commit was successful but push failed. Try running 'git push' manually.")
        return CliResult(None, 1)
    except ValueError:
        print_error("No remote named 'origin' found")
        print("Commit was successful but push failed. Configure a remote first.")
        return CliResult(None, 1)


def main() -> int:
    """Main entry point for syncing notes."""
    args = _parse_args()
    root_dir = get_root_dir()

    if (repo_result := _get_repository(root_dir)).is_error():
        return repo_result.code
    repo = repo_result.unwrap()

    print("Checking for modified notes...")
    modified_notes = _get_modified_notes(repo)

    if not modified_notes:
        print("No notes to sync")
        return 0

    print(f"Found {len(modified_notes)} modified note(s)")

    print("Updating timestamps...")
    updated_count = _update_note_timestamps(modified_notes)
    if updated_count > 0:
        print(f"Updated timestamps in {updated_count} note(s)")

    print("Staging changes...")
    if (stage_result := _stage_all_changes(repo)).is_error():
        return stage_result.code

    if not repo.is_dirty(untracked_files=True):
        print("No changes to commit")
        return 0

    commit_message = args.message or _generate_commit_message(modified_notes)
    print(f"Committing: {commit_message}")

    if (commit_result := _commit_changes(repo, commit_message)).is_error():
        return commit_result.code

    if not args.no_push:
        print("Pushing to remote...")
        if (push_result := _push_to_remote(repo)).is_error():
            return push_result.code
        print("Successfully synced notes!")
    else:
        print("Changes committed (not pushed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
