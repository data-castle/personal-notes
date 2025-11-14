import sys
from unittest.mock import patch

import pytest

from src.sync import (
    _add_note_to_list,
    _is_note_file,
    _update_timestamp_in_note,
    main,
)


@pytest.mark.parametrize(
    "path_str,expected",
    [
        ("notes/2025/test.md", True),
        ("notes/test.md", True),
        ("docs/readme.md", False),
        ("notes/test.txt", False),
        ("test.md", False),
        ("", False),
    ],
)
def test_is_note_file(path_str, expected):
    assert _is_note_file(path_str) == expected


def test_add_note_to_list_adds_existing_file(tmp_path):
    note_path = tmp_path / "test.md"
    note_path.write_text("test content")
    notes_list = []

    result = _add_note_to_list("test.md", notes_list, tmp_path, require_exists=True)

    assert len(result) == 1
    assert result[0] == note_path


def test_add_note_to_list_skips_nonexistent_file(tmp_path):
    notes_list = []

    result = _add_note_to_list(
        "nonexistent.md", notes_list, tmp_path, require_exists=True
    )

    assert len(result) == 0


def test_add_note_to_list_skips_duplicate(tmp_path):
    note_path = tmp_path / "test.md"
    note_path.write_text("test content")
    notes_list = [note_path]

    result = _add_note_to_list("test.md", notes_list, tmp_path, require_exists=True)

    assert len(result) == 1


def test_update_timestamp_in_note_updates_timestamp(tmp_path):
    note_path = tmp_path / "note.md"
    original_content = """---
title: "Test Note"
---

## Metadata
- **Created:** 2025-01-13 10:00
- **Last updated:** 2025-01-13 10:00

Content here.
"""
    note_path.write_text(original_content)

    result = _update_timestamp_in_note(note_path)

    assert not result.is_error()
    assert result.unwrap() is True
    updated_content = note_path.read_text()
    assert "2025-01-13 10:00" in updated_content
    assert updated_content != original_content


def test_update_timestamp_in_note_returns_false_when_no_timestamp_found(tmp_path):
    note_path = tmp_path / "note.md"
    note_path.write_text("# Note\n\nNo timestamp here.")

    result = _update_timestamp_in_note(note_path)

    assert not result.is_error()
    assert result.unwrap() is False


def test_update_timestamp_in_note_handles_missing_file(tmp_path, capsys):
    note_path = tmp_path / "nonexistent.md"

    result = _update_timestamp_in_note(note_path)

    assert not result.is_error()
    assert result.unwrap() is False
    captured = capsys.readouterr()
    assert "Warning" in captured.err


def test_main_returns_error_when_not_in_git_repo(tmp_path, capsys):
    with patch.object(sys, "argv", ["sync"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Not in a git repository" in captured.err


def test_main_returns_zero_when_no_notes_modified(
    tmp_path, git_repo_with_commit, capsys
):
    with patch.object(sys, "argv", ["sync"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No notes to sync" in captured.out


def test_main_syncs_modified_notes(tmp_path, git_repo_with_commit, create_note, capsys):
    create_note(content="Content")

    with patch.object(sys, "argv", ["sync", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Found 1 modified note(s)" in captured.out
    assert "Changes committed" in captured.out


def test_main_with_custom_commit_message(
    tmp_path, git_repo_with_commit, create_note, capsys
):
    create_note(content="Content")

    with patch.object(sys, "argv", ["sync", "-m", "Custom message", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Committing: Custom message" in captured.out


def test_main_handles_no_changes_after_staging(tmp_path, git_repo_with_commit, capsys):
    notes_dir = tmp_path / "notes" / "2025"
    notes_dir.mkdir(parents=True)
    note_path = notes_dir / "test-note.md"
    note_path.write_text("# Test\n\nContent without timestamp")

    git_repo_with_commit.index.add([str(note_path)])
    git_repo_with_commit.index.commit("Add note without timestamp")

    with patch.object(sys, "argv", ["sync"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Successfully pushed commits!" in captured.out


def test_sync_only_stages_notes_not_other_files(
    tmp_path, git_repo_with_commit, create_note, capsys
):
    create_note(content="Content")

    # Create files OUTSIDE notes folder that should be ignored
    other_file = tmp_path / "src" / "other.py"
    other_file.parent.mkdir(parents=True, exist_ok=True)
    other_file.write_text("# Some other file")

    config_file = tmp_path / "_config.yml"
    config_file.write_text("config: value")

    with patch.object(sys, "argv", ["sync", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Found 1 modified note(s)" in captured.out

    # Verify only the note was staged/committed
    last_commit = list(git_repo_with_commit.iter_commits(max_count=1))[0]
    committed_files = list(last_commit.stats.files.keys())

    # Only the note should be in the commit
    assert len(committed_files) == 1
    assert "notes/2025/test-note.md" in committed_files[0]

    # Other files should still be untracked
    assert "src/other.py" in git_repo_with_commit.untracked_files
    assert "_config.yml" in git_repo_with_commit.untracked_files
