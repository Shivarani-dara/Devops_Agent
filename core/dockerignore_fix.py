import os


def select_dockerignore_fix(
    debug_type,
    diagnostics,
    dockerignore_content,
    project_info,
    app_file="",
):
    """
    Return a deterministic .dockerignore fix only when diagnostics confirm
    that an existing project entry file is excluded by one unique,
    exact filename rule.

    Return None when the evidence is insufficient or ambiguous.
    This function never modifies files.
    """
    if debug_type not in ("docker_build", "docker_runtime"):
        return None

    if not diagnostics:
        return None

    if "Project entry file listed in .dockerignore: True" not in diagnostics:
        return None

    if dockerignore_content == "No .dockerignore file exists.":
        return None

    def diagnostic_value(label):
        for line in diagnostics.splitlines():
            if line.strip().startswith(label + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    entry_file = os.path.basename(
        diagnostic_value("Project entry file")
        or project_info.get("entry_point", "")
        or app_file
    )

    if not entry_file:
        return None

    project_files = project_info.get("files", [])
    entry_exists = entry_file in [
        os.path.basename(str(item)) for item in project_files
    ]

    exact_rules = [
        line
        for line in dockerignore_content.splitlines()
        if line.strip() == entry_file
    ]

    if not entry_exists or len(exact_rules) != 1:
        return None

    return {
        "file": ".dockerignore",
        "old": exact_rules[0],
        "new": "",
        "reason": (
            f"Diagnostics confirm that the existing entry file "
            f"'{entry_file}' is excluded by this unique exact "
            ".dockerignore rule. Remove the rule."
        ),
        "_deterministic": True,
    }
