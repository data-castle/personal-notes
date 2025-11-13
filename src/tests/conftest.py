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
