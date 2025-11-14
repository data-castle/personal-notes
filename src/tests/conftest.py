from collections.abc import Callable
from pathlib import Path

import git
import pytest


@pytest.fixture
def git_repo_with_commit(tmp_path) -> git.Repo:
    """Create a git repo with an initial commit (HEAD exists) and a mock remote."""
    # Create a bare repo to act as remote
    remote_path = tmp_path / ".remote"
    remote_path.mkdir()
    git.Repo.init(remote_path, bare=True)

    # Create the main repo
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Add the bare repo as origin remote
    repo.create_remote("origin", str(remote_path))

    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test")
    repo.index.add([str(readme)])
    repo.index.commit("Initial commit")

    # Push to remote to set up tracking
    current_branch = repo.active_branch
    branch_name = current_branch.name
    origin = repo.remote("origin")
    origin.push(f"{branch_name}:{branch_name}")

    # Set up tracking branch
    current_branch.set_tracking_branch(origin.refs[branch_name])

    return repo


@pytest.fixture
def note_template(tmp_path) -> Path:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "note_template.md"
    template_file.write_text(
        """---
title: "{{TITLE}}"
date: {{DATE}}
tags: [{{TAGS}}]
summary: "{{SHORT_DESCRIPTION}}"
---

## Metadata
- **Created:** {{DATE}} {{TIME}}
- **Last updated:** {{DATE}} {{TIME}}
- **Status:** Draft
- **Category:** {{CATEGORY}}

---

## Context
Add context here.

---

## Notes
- Point 1
- Point 2

---

## References
- [Link](#)

---

## Reflections
Write your reflections.
"""
    )
    return template_file


@pytest.fixture
def create_note(tmp_path) -> Callable[..., Path]:
    def _create_note(
        title: str = "Test Note",
        date: str = "2025-01-13",
        time: str = "10:00",
        content: str = "Content here.",
        filename: str | None = None,
        year: str = "2025",
    ) -> Path:
        """Create a note file and return its path."""
        notes_dir = tmp_path / "notes" / year
        notes_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = "test-note.md"

        note_path = notes_dir / filename
        note_path.write_text(
            f"""---
title: "{title}"
---

## Metadata
- **Created:** {date} {time}
- **Last updated:** {date} {time}

{content}
"""
        )
        return note_path

    return _create_note
