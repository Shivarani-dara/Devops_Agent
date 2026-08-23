import subprocess


def run_tests(project_path):
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


if __name__ == "__main__":

    result = run_tests("test_project")

    print("===== TEST OUTPUT =====")
    print(result["stdout"])

    print("===== TEST ERROR =====")
    print(result["stderr"])

    print("===== RETURN CODE =====")
    print(result["returncode"])