import sys
import time
from unittest.mock import patch

from src.new_note import main as new_note_main
from src.sync import main as sync_main


def test_integration_new_note_and_sync(
    tmp_path, git_repo_with_commit, note_template, capsys
):
    """Full integration test: create note with new_note → sync → modify → sync again."""
    # Step 1: Create a new note using new_note
    with patch.object(sys, "argv", ["new_note", "Integration Test", "--tags", "test"]):
        with patch("src.new_note.get_root_dir", return_value=tmp_path):
            exit_code = new_note_main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Created note:" in captured.out

    # Find the created note
    notes_dir = tmp_path / "notes"
    assert notes_dir.exists()
    year_dirs = list(notes_dir.iterdir())
    assert len(year_dirs) == 1
    note_files = list(year_dirs[0].glob("*.md"))
    assert len(note_files) == 1
    note_path = note_files[0]

    # Verify note content
    note_content = note_path.read_text()
    assert "Integration Test" in note_content
    assert "test" in note_content

    # Step 2: First sync (should commit the new note)
    with patch.object(sys, "argv", ["sync", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = sync_main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Found 1 modified note(s)" in captured.out
    assert "Changes committed" in captured.out

    # Verify commit was created
    commits = list(git_repo_with_commit.iter_commits(max_count=2))
    assert len(commits) == 2  # README + sync commit
    assert "Integration Test" in commits[0].message

    # Get timestamp from first sync
    first_sync_content = note_path.read_text()

    # Step 3: Modify the note
    time.sleep(0.1)  # Ensure timestamp difference
    modified_content = first_sync_content.replace(
        "**Category:** default", "**Category:** default\n\nModified content added here."
    )
    note_path.write_text(modified_content)

    # Step 4: Second sync (should detect modification)
    with patch.object(sys, "argv", ["sync", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = sync_main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Found 1 modified note(s)" in captured.out
    assert "Updated timestamps in 1 note(s)" in captured.out
    assert "Changes committed" in captured.out

    # Verify second commit
    commits = list(git_repo_with_commit.iter_commits(max_count=3))
    assert len(commits) == 3  # README + 2 sync commits

    # Verify modifications persisted
    final_content = note_path.read_text()
    assert "Modified content added here." in final_content
    assert final_content != first_sync_content

    # Step 5: Delete the note
    note_path.unlink()
    assert not note_path.exists()

    # Step 6: Third sync (should detect and commit deletion)
    with patch.object(sys, "argv", ["sync", "--no-push"]):
        with patch("src.sync.get_root_dir", return_value=tmp_path):
            exit_code = sync_main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Found 1 modified note(s)" in captured.out
    assert "Changes committed" in captured.out

    # Verify third commit for deletion
    commits = list(git_repo_with_commit.iter_commits(max_count=4))
    assert len(commits) == 4  # README + 3 sync commits

    # Verify the file is not in the repository anymore
    assert not note_path.exists()
    # Verify file is not in the git tree of the latest commit
    tree = commits[0].tree
    note_relative_path = str(note_path.relative_to(tmp_path))
    assert note_relative_path not in [item.path for item in tree.traverse()]
