# Personal Notes

A simple, git-based personal note-taking system with automatic timestamping and syncing.
Store your knowledge, track it with git, and optionally publish with GitHub Pages.

## Features

- **Timestamped Notes**: Every note includes creation and last-updated timestamps
- **Template-Based**: Consistent structure for all notes
- **Year-Based Organization**: Notes organized by year for easy navigation
- **Auto-Sync**: Automatic timestamp updates and git syncing
- **GitHub Pages Ready**: Optional publishing with Jekyll

## Quick Start

### 1. Use This Template

Click the "Use this template" button at the top of this repository to create your own personal notes repository.

### 2. Clone Your Repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd YOUR-REPO-NAME
```

### 3. Install Dependencies

This project uses [UV](https://docs.astral.sh/uv/) for Python package management:

```bash
# Install project dependencies
uv sync
```

### 4. Create Your First Note

```bash
uv run new-note "My First Note"
```

This creates a new note at `notes/YYYY/YYYY-MM-DD-my-first-note.md` with the template structure.

### 5. Edit Your Note

Open the generated note in your favorite editor and add your content.

### 6. Sync Your Notes

```bash
uv run sync
```

This will:
1. Update the "Last updated" timestamp in modified notes
2. Stage all changes
3. Commit with an auto-generated message
4. Push to remote

## Usage

### Creating Notes

Basic usage:

```bash
uv run new-note "Your Note Title"
```

With options:

```bash
uv run new-note "Your Note Title" --tags "python,coding" --category "development" --summary "A quick note about Python"
```

### Syncing Notes

Sync with auto-generated commit message:

```bash
uv run sync
```

Sync with custom commit message:

```bash
uv run sync -m "Weekly review and updates"
```

Commit without pushing:

```bash
uv run sync --no-push
```

## Note Template

Each note includes:

- **Title and metadata**: Date, tags, summary
- **Context section**: Background information
- **Notes section**: Main content
- **References**: Links and resources
- **Reflections**: Thoughts and insights

## GitHub Pages (Optional)

To publish your notes as a website:

1. Go to your repository settings
2. Navigate to "Pages" in the sidebar
3. Select source: "Deploy from a branch"
4. Select branch: `main` and folder: `/` (root)
5. Click "Save"

Your notes will be published at `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`

Note: Consider making your repository private if you want private notes with public pages.

## Development

### Running Tests

```bash
uv run pytest
```

## Customization

### Modify the Template

Edit `templates/note_template.md` to customize the structure of new notes.

### Change Jekyll Theme

Edit `_config.yml` to change the theme or other Jekyll settings.

## Requirements

- Python 3.13+
- Git
- UV (Python package manager)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
