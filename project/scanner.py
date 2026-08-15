import os


def scan_project(project_path):

    if not os.path.isdir(project_path):
        raise ValueError(
            f"Project directory not found: {project_path}"
        )

    files = os.listdir(project_path)

    project_info = {
        "project_path": project_path,
        "files": files,
        "type": "unknown",
        "entry_point": None,
        "requirements_file": None,
        "test_framework": None
    }

    # -----------------------------
    # Detect Python
    # -----------------------------

    if "requirements.txt" in files or any(
        file.endswith(".py") for file in files
    ):
        project_info["type"] = "python"

    # -----------------------------
    # Detect Node.js
    # -----------------------------

    if "package.json" in files:
        project_info["type"] = "node"

    # -----------------------------
    # Detect Java / Maven
    # -----------------------------

    if "pom.xml" in files:
        project_info["type"] = "java-maven"

    # -----------------------------
    # Detect Python entry point
    # -----------------------------

    if project_info["type"] == "python":

        if "app.py" in files:
            project_info["entry_point"] = "app.py"

        elif "main.py" in files:
            project_info["entry_point"] = "main.py"

    # -----------------------------
    # Dependencies
    # -----------------------------

    if "requirements.txt" in files:
        project_info["requirements_file"] = "requirements.txt"

    # -----------------------------
    # Detect pytest
    # -----------------------------

    if (
        "pytest.ini" in files
        or "pyproject.toml" in files
        or "tests" in files
    ):
        project_info["test_framework"] = "pytest"

    return project_info



if __name__ == "__main__":

    import sys

    project_path = sys.argv[1]

    info = scan_project(project_path)

    print("\n===== PROJECT INFORMATION =====")

    for key, value in info.items():
        print(f"{key}: {value}")