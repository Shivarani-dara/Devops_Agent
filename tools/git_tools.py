import subprocess
from pathlib import Path


def git_status(project_path):
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def git_checkpoint(project_path):
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if status.returncode != 0:
        return {
            "success": False,
            "error": status.stderr
        }

    # Save current changes if there are any
    if status.stdout.strip():
        result = subprocess.run(
            ["git", "add", "-A"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

        result = subprocess.run(
            ["git", "commit", "-m", "AI debugging checkpoint"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr
            }

    # Get the exact HEAD commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "error": result.stderr
        }

    return {
        "success": True,
        "checkpoint": result.stdout.strip()
    }

def git_rollback(project_path, checkpoint):
    result = subprocess.run(
        ["git", "reset", "--hard", checkpoint],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def git_commit_success(project_path):
    """
    Commit a fix after the application and tests pass.

    A successful result requires an actual Git commit to be created.
    """

    # Get the current HEAD before committing.
    before = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if before.returncode != 0:
        return {
            "success": False,
            "stdout": "",
            "stderr": before.stderr
        }

    before_head = before.stdout.strip()

    # Check if there are changes to commit.
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if status.returncode != 0:
        return {
            "success": False,
            "stdout": status.stdout,
            "stderr": status.stderr
        }

    # No changes means no commit was created.
    if status.stdout.strip() == "":
        return {
            "success": False,
            "stdout": "",
            "stderr": "No changes to commit. No new Git commit was created."
        }

    # Stage changes.
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    # Create commit.
    result = subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "AI debugging fix"
        ],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    # Get HEAD after committing.
    after = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if after.returncode != 0:
        return {
            "success": False,
            "stdout": result.stdout,
            "stderr": after.stderr
        }

    after_head = after.stdout.strip()

    # A real commit must change HEAD.
    if before_head == after_head:
        return {
            "success": False,
            "stdout": result.stdout,
            "stderr": "Git commit command succeeded, but HEAD did not change."
        }

    return {
        "success": True,
        "stdout": result.stdout,
        "stderr": ""
    }



def git_repo_root(project_path):
    """
    Return the absolute Git repository root for the given project path.
    """

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "root": "",
            "error": result.stderr.strip()
        }

    return {
        "success": True,
        "root": result.stdout.strip(),
        "error": ""
    }


def git_commit_file(project_path, file_path, message):
    """
    Commit only the specified file.

    The project path may be a subdirectory of the Git repository,
    so the file path is resolved relative to the repository root.
    """

    repo_result = git_repo_root(project_path)

    if not repo_result["success"]:
        return {
            "success": False,
            "stdout": "",
            "stderr": repo_result["error"]
        }

    repo_root = Path(repo_result["root"]).resolve()
    file_path_obj = Path(file_path)

    if file_path_obj.is_absolute():
        absolute_file = file_path_obj.resolve()
    else:
        absolute_file = (repo_root / file_path_obj).resolve()

    try:
        git_file_path = absolute_file.relative_to(repo_root)
    except ValueError:
        return {
            "success": False,
            "stdout": "",
            "stderr": (
                f"File is outside the Git repository: "
                f"{absolute_file}"
            )
        }

    git_file_path = str(git_file_path)

    status = subprocess.run(
        ["git", "status", "--short", "--", git_file_path],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if status.returncode != 0:
        return {
            "success": False,
            "stdout": status.stdout,
            "stderr": status.stderr
        }

    if not status.stdout.strip():
        return {
            "success": False,
            "stdout": "",
            "stderr": f"No changes found for {git_file_path}."
        }

    result = subprocess.run(
        ["git", "add", "--", git_file_path],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def git_push(project_path, remote="origin", branch="main"):
    """
    Push the specified branch to the remote repository.
    """

    result = subprocess.run(
        ["git", "push", remote, branch],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


if __name__ == "__main__":

    project_path = "/home/darashivarani/calculator"

    print("===== GIT STATUS =====")
    print(git_status(project_path))

    print("\n===== CREATING CHECKPOINT =====")
    print(git_checkpoint(project_path))

    print("\n===== GIT STATUS AFTER CHECKPOINT =====")
    print(git_status(project_path))