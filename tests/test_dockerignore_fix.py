from core.dockerignore_fix import select_dockerignore_fix
from core.validator import validate_dockerignore_fix


def test_unique_excluded_entry_gets_deterministic_fix():
    diagnostics = (
        "Project entry file: app.py\n"
        "Project entry file exists: True\n"
        "Project entry file listed in .dockerignore: True"
    )
    project_info = {"files": ["app.py", "requirements.txt"]}
    content = "app.py\n__pycache__/\n"

    fix = select_dockerignore_fix(
        debug_type="docker_build",
        diagnostics=diagnostics,
        dockerignore_content=content,
        project_info=project_info,
        app_file="app.py",
    )

    assert fix is not None
    assert fix["file"] == ".dockerignore"
    assert fix["old"] == "app.py"
    assert fix["new"] == ""
    assert fix["_deterministic"] is True

    result = validate_dockerignore_fix(
        content, fix["old"], fix["new"]
    )
    assert result["valid"] is True


def test_duplicate_exact_rules_are_rejected():
    diagnostics = (
        "Project entry file: app.py\n"
        "Project entry file exists: True\n"
        "Project entry file listed in .dockerignore: True"
    )

    fix = select_dockerignore_fix(
        debug_type="docker_build",
        diagnostics=diagnostics,
        dockerignore_content="app.py\napp.py\n",
        project_info={"files": ["app.py"]},
        app_file="app.py",
    )

    assert fix is None


def test_missing_diagnostic_evidence_is_rejected():
    fix = select_dockerignore_fix(
        debug_type="docker_build",
        diagnostics="",
        dockerignore_content="app.py\n",
        project_info={"files": ["app.py"]},
        app_file="app.py",
    )

    assert fix is None


if __name__ == "__main__":
    test_unique_excluded_entry_gets_deterministic_fix()
    test_duplicate_exact_rules_are_rejected()
    test_missing_diagnostic_evidence_is_rejected()
    print("All dockerignore regression tests passed.")
