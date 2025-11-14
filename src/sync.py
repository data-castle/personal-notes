"""Sync notes by updating timestamps, committing, and pushing to remote."""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from git import Repo, diff as git_diff
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


def _update_timestamp_in_note(file_path: Path) -> CliResult[bool]:
    """Update the 'Last updated' timestamp in a note file."""
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
            return CliResult(True, 0)

        return CliResult(False, 0)

    except (OSError, IOError) as e:
        print(
            f"Warning: Could not update timestamp in {file_path}: {e}", file=sys.stderr
        )
        return CliResult(False, 0)


def _is_note_file(path_str: str) -> bool:
    """Check if a path string represents a note markdown file."""
    path = Path(path_str)
    return (
        (len(path.parts) > 0) and (path.parts[0] == "notes") and (path.suffix == ".md")
    )


def _add_note_to_list(
    path_str: str, notes_list: list[Path], repo_root: Path, require_exists: bool = True
) -> list[Path]:
    """Add a note file path to the list if it exists and is not already present."""
    file_path = repo_root / path_str
    if file_path not in notes_list:
        if not require_exists or file_path.exists():
            notes_list.append(file_path)
    return notes_list


def _add_note_from_diff(
    diff: git_diff.Diff, notes_list: list[Path], repo_root: Path
) -> list[Path]:
    """Add a note from a git diff to the list, handling deletions."""
    return _add_note_to_list(
        diff.a_path, notes_list, repo_root, require_exists=not diff.deleted_file
    )


def _get_modified_notes(repo: Repo) -> list[Path]:
    """Get list of modified markdown files in notes/ directory."""
    modified_files: list[Path] = []
    repo_root = Path(repo.working_dir)

    # Get untracked files
    for item in repo.untracked_files:
        if _is_note_file(item):
            modified_files = _add_note_to_list(
                item, modified_files, repo_root, require_exists=True
            )

    # Get modified files from diff (unstaged changes)
    for diff in repo.index.diff(None):
        if _is_note_file(diff.a_path):
            modified_files = _add_note_from_diff(diff, modified_files, repo_root)

    # Get staged files
    for diff in repo.index.diff("HEAD"):
        if diff.a_path and _is_note_file(diff.a_path):
            modified_files = _add_note_from_diff(diff, modified_files, repo_root)

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
            if title_match is not None:
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


def _update_note_timestamps(modified_notes: list[Path]) -> CliResult[int]:
    """Update timestamps in modified notes. Returns CliResult with count of updated notes."""
    updated_count = 0
    for note in modified_notes:
        if not note.exists():
            continue
        result = _update_timestamp_in_note(note)
        if not result.is_error() and result.unwrap():
            updated_count += 1
    return CliResult(updated_count, 0)


def _validate_note_path(note_path: Path, repo_root: Path) -> bool:
    """Validate that a note path is safe and within the repository."""
    try:
        abs_note_path = note_path.resolve()
        abs_repo_root = repo_root.resolve()
        abs_note_path.relative_to(abs_repo_root)

        # Additional check: path should be under notes/ directory
        rel_path = (
            note_path.relative_to(repo_root) if note_path.is_absolute() else note_path
        )
        return len(rel_path.parts) > 0 and rel_path.parts[0] == "notes"
    except (ValueError, OSError):
        return False


def _stage_notes(repo: Repo, notes: list[Path], repo_root: Path) -> CliResult[bool]:
    """Stage only the specified note files with path validation."""
    try:
        for note in notes:
            if not _validate_note_path(note, repo_root):
                print_error(f"Invalid note path: {note}")
                return CliResult(False, 1)
            repo.git.add(str(note))
        return CliResult(True, 0)
    except GitCommandError as e:
        print_error(f"Staging changes: {e}")
        return CliResult(False, 1)


def _commit_changes(repo: Repo, message: str) -> CliResult[bool]:
    """Commit staged changes with the given message.

    Skips formatter/linter hooks but keeps security checks:
    - Skipped: ruff, ruff-format, trailing-whitespace, end-of-file-fixer
    - Runs: check-docstring-first, check-merge-conflict, check-toml, requirements-txt-fixer
    """
    try:
        env = os.environ.copy()
        env["SKIP"] = "ruff,ruff-format,trailing-whitespace,end-of-file-fixer"
        with repo.git.custom_environment(**env):
            repo.index.commit(message, skip_hooks=False)

        return CliResult(True, 0)
    except GitCommandError as e:
        print_error(f"Committing changes: {e}")
        return CliResult(False, 1)


def _has_unpushed_commits(repo: Repo) -> bool:
    """Check if there are local commits not pushed to remote.

    Returns:
        True if there are unpushed commits, False otherwise
    """
    try:
        current_branch = repo.active_branch
        branch_name = current_branch.name

        if current_branch.tracking_branch() is None:
            # No remote tracking branch - consider it as having unpushed commits if we have commits
            return len(list(repo.iter_commits(max_count=1))) > 0

        # Compare local and remote branches
        remote_branch = current_branch.tracking_branch().name
        commits_ahead = list(repo.iter_commits(f"{remote_branch}..{branch_name}"))
        return len(commits_ahead) > 0
    except (ValueError, GitCommandError):
        # If we can't determine, assume no unpushed commits
        return False


def _push_to_remote(repo: Repo) -> CliResult[bool]:
    """Push commits to the remote origin."""
    try:
        origin = repo.remote(name="origin")
        origin.push()
        return CliResult(True, 0)
    except GitCommandError as e:
        print_error(f"Pushing to remote: {e}")
        print("Push failed. Run sync again to retry pushing.")
        return CliResult(False, 1)


def _handle_no_modified_notes(repo: Repo, should_push: bool) -> int:
    """Handle case when no modified notes are found.

    Args:
        repo: Git repository instance
        should_push: Whether to attempt pushing (False if --no-push flag set)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Check if there are unpushed commits to push
    if should_push and _has_unpushed_commits(repo):
        print("No modified notes, but found unpushed commits")
        print("Pushing to remote...")
        if (push_result := _push_to_remote(repo)).is_error():
            return push_result.code
        print("Successfully pushed commits!")
        return 0

    print("No notes to sync")
    return 0


def _sync_modified_notes(
    repo: Repo, modified_notes: list[Path], root_dir: Path, custom_message: str | None
) -> CliResult[bool]:
    """Update timestamps, stage, and commit modified notes.

    Args:
        repo: Git repository instance
        modified_notes: List of modified note files
        root_dir: Root directory of the repository
        custom_message: Optional custom commit message

    Returns:
        CliResult with True if changes were committed, False if no changes to commit
    """
    # Update timestamps
    print("Updating timestamps...")
    timestamp_result = _update_note_timestamps(modified_notes)
    if not timestamp_result.is_error():
        updated_count = timestamp_result.unwrap()
        if updated_count > 0:
            print(f"Updated timestamps in {updated_count} note(s)")

    # Stage changes
    print("Staging changes...")
    if (stage_result := _stage_notes(repo, modified_notes, root_dir)).is_error():
        return stage_result

    # Check if there are staged changes
    staged_diff = repo.index.diff("HEAD")
    if len(staged_diff) == 0:
        print("No changes to commit")
        return CliResult(False, 0)

    # Commit changes
    commit_message = custom_message or _generate_commit_message(modified_notes)
    print(f"Committing: {commit_message}")
    if (commit_result := _commit_changes(repo, commit_message)).is_error():
        return commit_result

    return CliResult(True, 0)


def main() -> int:
    """Main entry point for syncing notes."""
    args = _parse_args()
    root_dir = get_root_dir()

    if (repo_result := _get_repository(root_dir)).is_error():
        return repo_result.code
    repo = repo_result.unwrap()

    print("Checking for modified notes...")
    modified_notes = _get_modified_notes(repo)

    if len(modified_notes) == 0:
        return _handle_no_modified_notes(repo, not args.no_push)

    print(f"Found {len(modified_notes)} modified note(s)")

    # Sync modified notes (update timestamps, stage, commit)
    sync_result = _sync_modified_notes(repo, modified_notes, root_dir, args.message)
    if sync_result.is_error():
        return sync_result.code

    committed = sync_result.unwrap()
    if not committed:
        # No changes were actually committed
        return 0

    # Push to remote if requested
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
