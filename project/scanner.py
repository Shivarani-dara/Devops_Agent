import os


def scan_project(project_path):

    if not os.path.isdir(project_path):
        raise ValueError(
            f"Project directory not found: {project_path}"
        )

    # ============================================================
    # FIND ALL FILES RECURSIVELY
    # ============================================================

    all_files = []

    for root, dirs, files in os.walk(project_path):

        # Ignore unnecessary directories
        dirs[:] = [
            d for d in dirs
            if d not in {
                "__pycache__",
                ".pytest_cache",
                ".git",
                "venv",
                ".venv"
            }
        ]

        for file in files:

            full_path = os.path.join(root, file)

            relative_path = os.path.relpath(
                full_path,
                project_path
            )

            all_files.append(relative_path)

    # ============================================================
    # PROJECT INFORMATION
    # ============================================================

    project_info = {
        "project_path": project_path,
        "files": all_files,

        "type": "unknown",

        "entry_point": None,

        "requirements_file": None,

        "test_framework": None,

        "source_files": [],

        "test_files": [],

        "dockerfile": None,
        "dockerignore": None,
        "jenkinsfile": None
            }

    # ============================================================
    # DETECT PYTHON
    # ============================================================

    if any(file.endswith(".py") for file in all_files):

        project_info["type"] = "python"

    # ============================================================
    # DEVOPS FILES
    # ============================================================

    if "Dockerfile" in all_files:
        project_info["dockerfile"] = "Dockerfile"

    if ".dockerignore" in all_files:
        project_info["dockerignore"] = ".dockerignore"

    jenkinsfiles = [
        file for file in all_files
        if os.path.basename(file) == "Jenkinsfile"
    ]

    if jenkinsfiles:
        project_info["jenkinsfile"] = jenkinsfiles[0]

    # ============================================================
    # DETECT NODE.JS
    # ============================================================

    if "package.json" in all_files:

        project_info["type"] = "node"

    # ============================================================
    # DETECT JAVA / MAVEN
    # ============================================================

    if "pom.xml" in all_files:

        project_info["type"] = "java-maven"

    

    # ============================================================
    # PYTHON PROJECT
    # ============================================================

    if project_info["type"] == "python":

        # --------------------------------------------------------
        # Find Python source files
        # --------------------------------------------------------

        for file in all_files:

            if not file.endswith(".py"):
                continue

            # Ignore test files
            if (
                file.startswith("tests/")
                or file.startswith("test/")
                or os.path.basename(file).startswith("test_")
                or os.path.basename(file).endswith("_test.py")
            ):
                continue

            project_info["source_files"].append(file)

        # --------------------------------------------------------
        # Find test files
        # --------------------------------------------------------

        for file in all_files:

            if not file.endswith(".py"):
                continue

            filename = os.path.basename(file)

            if (
                file.startswith("tests/")
                or file.startswith("test/")
                or filename.startswith("test_")
                or filename.endswith("_test.py")
            ):
                project_info["test_files"].append(file)

        # --------------------------------------------------------
        # Detect entry point
        # --------------------------------------------------------

        if "app.py" in all_files:

            project_info["entry_point"] = "app.py"

        elif "main.py" in all_files:

            project_info["entry_point"] = "main.py"

        elif "__main__.py" in all_files:

            project_info["entry_point"] = "__main__.py"

        # --------------------------------------------------------
        # Requirements
        # --------------------------------------------------------

        if "requirements.txt" in all_files:

            project_info["requirements_file"] = "requirements.txt"

        # --------------------------------------------------------
        # Detect pytest
        # --------------------------------------------------------

        if (
            "pytest.ini" in all_files
            or "pyproject.toml" in all_files
            or len(project_info["test_files"]) > 0
        ):
            project_info["test_framework"] = "pytest"

    return project_info


def scan_repository(repository_path):
    """
    Discover project directories inside a repository.
    """

    if not os.path.isdir(repository_path):
        raise ValueError(
            f"Repository directory not found: {repository_path}"
        )

    project_markers = {
        "package.json",
        "pom.xml",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "Dockerfile",
        "Jenkinsfile",
    }

    discovered_projects = []

    for root, dirs, files in os.walk(repository_path):

        dirs[:] = [
            d for d in dirs
            if d not in {
                ".git",
                "__pycache__",
                ".pytest_cache",
                "venv",
                ".venv",
                "node_modules"
            }
        ]

        strong_markers = {
            "package.json",
            "pom.xml",
            "pyproject.toml",
            "setup.py",
            "Dockerfile",
            "Jenkinsfile",
        }

        if any(file in strong_markers for file in files):

            relative_path = os.path.relpath(
                root,
                repository_path
            )

            if relative_path == ".":
                relative_path = ""

            discovered_projects.append(relative_path)

    return discovered_projects


# ================================================================
# TEST SCANNER DIRECTLY
# ================================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) != 2:

        print("Usage: python3 scanner.py <project_path>")

        sys.exit(1)

    project_path = sys.argv[1]

    info = scan_project(project_path)

    print("\n===== PROJECT INFORMATION =====")

    for key, value in info.items():

        print(f"{key}: {value}")