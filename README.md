# Personal Notes

A simple, git-based personal note-taking system with automatic timestamping and syncing.

## Features

- Template-based notes with consistent structure
- Automatic timestamps (creation and last updated)
- Year-based organization (`notes/YYYY/`)
- Git sync that only commits note files
- Optional GitHub Pages publishing

## Quick Start

### 1. Use This Template

Click "Use this template" at the top of this repository to create your own personal notes.

### 2. Clone and Setup

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd YOUR-REPO-NAME
uv sync
```

### 3. Create a Note

```bash
uv run new-note "My First Note"
```

Options:
```bash
uv run new-note "My Note" --tags "python,coding" --category "development"
```

### 4. Sync Your Notes

```bash
uv run sync
```

This will update timestamps, commit, and push to git.

## Daily Usage

### Create a new note
```bash
uv run new-note "Note Title"
```

### Edit your notes
Open and edit files in `notes/YYYY/` with your favorite editor.

### Sync changes
```bash
uv run sync
```

The sync command:
- Updates "Last updated" timestamps
- Only commits files in `notes/` folder
- Auto-generates commit messages
- Pushes to remote

### Sync without pushing
```bash
uv run sync --no-push
```

### Custom commit message
```bash
uv run sync -m "Your message"
```

## Requirements

- Python 3.13+
- Git
- [UV](https://docs.astral.sh/uv/) package manager

## GitHub Pages (Optional)

To publish your notes:
1. Go to repository Settings → Pages
2. Select source: "Deploy from a branch"
3. Select branch: `main`, folder: `/` (root)
4. Click "Save"

Your notes will be at `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License
