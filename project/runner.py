from tools.command_tools import run_command


def run_project(project_info):

    project_path = project_info["project_path"]
    project_type = project_info["type"]
    entry_point = project_info["entry_point"]

    if project_type == "python":

        if entry_point is None:
            return {
                "stdout": "",
                "stderr": "ERROR: Python entry point not found.",
                "returncode": 1
            }

        command = f"python3 {entry_point}"

        return run_command(
            command,
            cwd=project_path
        )

    return {
        "stdout": "",
        "stderr": f"Unsupported project type: {project_type}",
        "returncode": 1
    }