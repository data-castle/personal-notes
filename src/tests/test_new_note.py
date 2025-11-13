import argparse
import sys
from unittest.mock import patch

import pytest

from src.new_note import (
    CliResult,
    _create_filename,
    _create_note_path,
    _get_template_path,
    _parse_args,
    _replace_template_placeholders,
    _slugify,
    _write_note_content,
    main,
)


def test_cli_result_is_error_returns_true_for_nonzero_code():
    result = CliResult(None, 1)
    assert result.is_error() is True


def test_cli_result_is_error_returns_false_for_zero_code():
    result = CliResult("value", 0)
    assert result.is_error() is False


def test_cli_result_unwrap_returns_value_when_present():
    result = CliResult("test_value", 0)
    assert result.unwrap() == "test_value"


def test_cli_result_unwrap_raises_assertion_when_value_is_none():
    result = CliResult(None, 1)
    with pytest.raises(AssertionError, match="Cannot unwrap an error result"):
        result.unwrap()


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("Hello World", "hello-world"),
        ("my great note", "my-great-note"),
        ("note@#$%with&*special!", "notewithspecial"),
        ("too    many    spaces", "too-many-spaces"),
        ("---note---", "note"),
        ("", ""),
        ("!@#$%^&*()", ""),
        ("Test123Note", "test123note"),
        ("café résumé", "café-résumé"),
    ],
)
def test_slugify(input_text, expected):
    assert _slugify(input_text) == expected


def test_get_template_path_returns_success_when_template_exists(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "note_template.md"
    template_file.write_text("test template")

    result = _get_template_path(tmp_path)
    assert not result.is_error()
    assert result.unwrap() == template_file


def test_get_template_path_returns_error_when_template_missing(tmp_path, capsys):
    result = _get_template_path(tmp_path)
    assert result.is_error()
    assert result.code == 1
    assert result.value is None

    captured = capsys.readouterr()
    assert "Error: Template not found" in captured.err


def test_create_filename_with_date_and_slug():
    filename = _create_filename("2025-01-13", "Test Note")
    assert filename.startswith("2025-01-13-test-note-")
    assert filename.endswith(".md")


def test_create_filename_includes_random_hash():
    filename1 = _create_filename("2025-01-13", "Test Note")
    filename2 = _create_filename("2025-01-13", "Test Note")
    assert filename1 != filename2


def test_create_filename_handles_empty_title():
    filename = _create_filename("2025-01-13", "")
    assert "untitled-note" in filename


def test_create_filename_handles_special_characters_in_title():
    filename = _create_filename("2025-01-13", "Test@#$Note!!!")
    assert "2025-01-13-testnote-" in filename


def test_create_filename_random_hash_length():
    filename = _create_filename("2025-01-13", "Test")
    parts = filename.replace(".md", "").split("-")
    hash_part = parts[-1]
    assert len(hash_part) == 6


def test_create_note_path_creates_directory_structure(tmp_path):
    filename = "2025-01-13-test-note-abc123.md"
    result = _create_note_path(tmp_path, filename, "2025")

    assert not result.is_error()
    expected_path = tmp_path / "notes" / "2025" / filename
    assert result.unwrap() == expected_path
    assert expected_path.parent.exists()
    assert expected_path.parent.is_dir()


def test_create_note_path_succeeds_when_directory_already_exists(tmp_path):
    notes_dir = tmp_path / "notes" / "2025"
    notes_dir.mkdir(parents=True)

    filename = "2025-01-13-test-note-abc123.md"
    result = _create_note_path(tmp_path, filename, "2025")

    assert not result.is_error()
    assert result.unwrap() == notes_dir / filename


def test_create_note_path_creates_nested_year_directories(tmp_path):
    filename = "2026-01-13-test-note-abc123.md"
    result = _create_note_path(tmp_path, filename, "2026")

    assert not result.is_error()
    expected_path = tmp_path / "notes" / "2026" / filename
    assert expected_path.parent.exists()


def test_replace_template_placeholders_replaces_all(tmp_path):
    template_file = tmp_path / "template.md"
    template_content = """---
title: "{{TITLE}}"
date: {{DATE}}
tags: [{{TAGS}}]
summary: "{{SHORT_DESCRIPTION}}"
---

## Metadata
- **Created:** {{DATE}} {{TIME}}
- **Category:** {{CATEGORY}}
"""
    template_file.write_text(template_content)

    args = argparse.Namespace(
        title="Test Note",
        tags="python,testing",
        summary="A test note",
        category="development",
    )

    result = _replace_template_placeholders(args, template_file, "2025-01-13", "14:30")

    assert not result.is_error()
    content = result.unwrap()

    assert "Test Note" in content
    assert "2025-01-13" in content
    assert "14:30" in content
    assert "python,testing" in content
    assert "A test note" in content
    assert "development" in content

    assert "{{" not in content
    assert "}}" not in content


def test_replace_template_placeholders_handles_missing_template_file(tmp_path, capsys):
    template_file = tmp_path / "nonexistent.md"
    args = argparse.Namespace(title="Test", tags="", summary="", category="")

    result = _replace_template_placeholders(args, template_file, "2025-01-13", "14:30")

    assert result.is_error()
    assert result.code == 1
    captured = capsys.readouterr()
    assert "Error: Failed to read template" in captured.err


def test_write_note_content_writes_content_to_file(tmp_path):
    note_path = tmp_path / "test-note.md"
    content = "# Test Note\n\nThis is test content."

    result = _write_note_content(note_path, content)

    assert not result.is_error()
    assert result.unwrap() == note_path
    assert note_path.exists()
    assert note_path.read_text(encoding="utf-8") == content


def test_write_note_content_uses_utf8_encoding(tmp_path):
    note_path = tmp_path / "unicode-note.md"
    content = "# Café ☕\n\n日本語 文字"

    result = _write_note_content(note_path, content)

    assert not result.is_error()
    written_content = note_path.read_text(encoding="utf-8")
    assert written_content == content


def test_write_note_content_fails_when_file_already_exists(tmp_path, capsys):
    note_path = tmp_path / "existing-note.md"
    note_path.write_text("existing content")

    result = _write_note_content(note_path, "new content")

    assert result.is_error()
    assert result.code == 1
    captured = capsys.readouterr()
    assert "Error: Note already exists" in captured.err

    assert note_path.read_text() == "existing content"


def test_write_note_content_creates_file_with_exclusive_mode(tmp_path):
    note_path = tmp_path / "exclusive-note.md"

    result = _write_note_content(note_path, "content")
    assert not result.is_error()

    result2 = _write_note_content(note_path, "different content")
    assert result2.is_error()


def test_parse_args_parses_all_arguments_together():
    with patch.object(
        sys,
        "argv",
        [
            "new_note.py",
            "Complete Test",
            "--tags",
            "a,b,c",
            "--category",
            "dev",
            "--summary",
            "Full test",
        ],
    ):
        args = _parse_args()
        assert args.title == "Complete Test"
        assert args.tags == "a,b,c"
        assert args.category == "dev"
        assert args.summary == "Full test"


def test_main_creates_note_successfully(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

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
- **Category:** {{CATEGORY}}
"""
    )

    with patch.object(sys, "argv", ["new_note.py", "Integration Test"]):
        with patch("src.new_note.pathlib.Path") as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            exit_code = main()

    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Created note:" in captured.out

    notes_dir = tmp_path / "notes"
    assert notes_dir.exists()

    year_dirs = list(notes_dir.iterdir())
    assert len(year_dirs) == 1

    note_files = list(year_dirs[0].glob("*.md"))
    assert len(note_files) == 1

    note_content = note_files[0].read_text()
    assert "Integration Test" in note_content
    assert "general" in note_content


def test_main_returns_error_when_template_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with patch.object(sys, "argv", ["new_note.py", "Test"]):
        with patch("src.new_note.pathlib.Path") as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            exit_code = main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: Template not found" in captured.err


def test_main_creates_note_with_custom_metadata(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "note_template.md"
    template_file.write_text(
        "{{TITLE}} - {{TAGS}} - {{CATEGORY}} - {{SHORT_DESCRIPTION}}"
    )

    with patch.object(
        sys,
        "argv",
        [
            "new_note.py",
            "Custom Note",
            "--tags",
            "custom,test",
            "--category",
            "testing",
            "--summary",
            "Custom summary",
        ],
    ):
        with patch("src.new_note.pathlib.Path") as mock_path:
            mock_path.return_value.parent.parent = tmp_path
            exit_code = main()

    assert exit_code == 0

    notes_dir = tmp_path / "notes"
    year_dirs = list(notes_dir.iterdir())
    note_files = list(year_dirs[0].glob("*.md"))
    note_content = note_files[0].read_text()

    assert "Custom Note" in note_content
    assert "custom,test" in note_content
    assert "testing" in note_content
    assert "Custom summary" in note_content
