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

if __name__ == "__main__":

    project_path = "/home/darashivarani/calculator"

    print("===== GIT STATUS =====")
    print(git_status(project_path))

    print("\n===== CREATING CHECKPOINT =====")
    print(git_checkpoint(project_path))

    print("\n===== GIT STATUS AFTER CHECKPOINT =====")
    print(git_status(project_path))