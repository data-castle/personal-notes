import git
import pytest


@pytest.fixture
def git_repo_with_commit(tmp_path):
    """Create a git repo with an initial commit (HEAD exists)."""
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test")
    repo.index.add([str(readme)])
    repo.index.commit("Initial commit")

    return repo


@pytest.fixture
def note_template(tmp_path):
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
def create_note(tmp_path):
    def _create_note(
        title="Test Note",
        date="2025-01-13",
        time="10:00",
        content="Content here.",
        filename=None,
        year="2025",
    ):
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
