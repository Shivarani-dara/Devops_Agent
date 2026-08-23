import subprocess


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
    If there's nothing to commit (no changes were made),
    treat that as success rather than a failure.
    """
    # Check if there are any changes to commit
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    if status.returncode != 0:
        return {
            "success": False,
            "stdout": "",
            "stderr": status.stderr
        }

    # Nothing changed — nothing to commit, and that's fine.
    if status.stdout.strip() == "":
        return {
            "success": True,
            "stdout": "No changes to commit. Already up to date.",
            "stderr": ""
        }

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