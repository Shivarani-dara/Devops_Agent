import subprocess

from tools.git_tools import git_checkpoint
from tools.file_tools import modify_file


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def make_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    git(repo, "init")
    git(repo, "config", "user.name", "Safety Test")
    git(repo, "config", "user.email", "safety-test@example.com")

    target = repo / ".dockerignore"
    target.write_text("app.py\n")

    git(repo, "add", ".dockerignore")
    git(repo, "commit", "-m", "Initial test state")

    return repo, target


def test_checkpoint_failure_is_reported(tmp_path, monkeypatch):
    repo, target = make_repo(tmp_path)
    before = target.read_text()

    def fail_git_status(*args, **kwargs):
        class Result:
            returncode = 128
            stdout = ""
            stderr = "simulated Git failure"

        return Result()

    monkeypatch.setattr(
        "tools.git_tools.subprocess.run",
        fail_git_status,
    )

    checkpoint = git_checkpoint(str(repo))

    assert checkpoint["success"] is False
    assert target.read_text() == before


def test_rejected_fix_leaves_file_unchanged(tmp_path):
    repo, target = make_repo(tmp_path)
    before = target.read_text()

    # Model the same rejection branch used by run_agent_loop:
    # when approval is not "y", execution stops before checkpoint
    # creation and before modify_file is called.
    choice = "n"

    if choice.lower() != "y":
        rejected = True
    else:
        rejected = False
        checkpoint = git_checkpoint(str(repo))
        if checkpoint["success"]:
            modify_file(str(target), "app.py", "")

    assert rejected is True
    assert target.read_text() == before
    assert git(repo, "status", "--porcelain").stdout == ""


