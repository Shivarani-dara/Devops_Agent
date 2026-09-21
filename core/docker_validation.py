import os
import re

from tools.docker_tools import build_and_run_docker


def analyze_docker_startup(
    dockerfile,
    project_path,
    project_info,
    dockerignore,
    error
):
    """
    Collect deterministic evidence about Docker container startup.

    This function does NOT decide or apply a fix.
    It only reports facts for the LLM to reason about.
    """

    diagnostics = []

    entry_point = project_info.get("entry_point", "")

    # --------------------------------------------------------
    # Check whether the runtime error looks like a missing file
    # --------------------------------------------------------

    missing_file_match = re.search(
        r"can't open file ['\"]([^'\"]+)['\"]",
        error,
        re.IGNORECASE
    )

    if not missing_file_match:
        return "No Python startup file-not-found pattern detected."

    requested_path = missing_file_match.group(1)
    requested_file = os.path.basename(requested_path)

    diagnostics.append(
        f"Runtime error references file: {requested_file}"
    )

    # --------------------------------------------------------
    # Extract CMD / ENTRYPOINT target from CURRENT Dockerfile
    # --------------------------------------------------------

    startup_target = None

    cmd_match = re.search(
        r'CMD\s*\[\s*"[^"]+"\s*,\s*"([^"]+)"\s*\]',
        dockerfile,
        re.IGNORECASE
    )

    entrypoint_match = re.search(
        r'ENTRYPOINT\s*\[\s*"[^"]+"\s*,\s*"([^"]+)"\s*\]',
        dockerfile,
        re.IGNORECASE
    )

    if cmd_match:
        startup_target = os.path.basename(cmd_match.group(1))
        diagnostics.append(
            f"CMD startup target: {startup_target}"
        )

    elif entrypoint_match:
        startup_target = os.path.basename(
            entrypoint_match.group(1)
        )
        diagnostics.append(
            f"ENTRYPOINT startup target: {startup_target}"
        )

    else:
        diagnostics.append(
            "No simple Python CMD/ENTRYPOINT startup target detected."
        )

    # --------------------------------------------------------
    # Check whether startup target exists in project
    # --------------------------------------------------------

    if startup_target:
        startup_file_path = os.path.join(
            project_path,
            startup_target
        )

        diagnostics.append(
            f"Startup target exists in project: "
            f"{os.path.exists(startup_file_path)}"
        )

    # --------------------------------------------------------
    # Compare startup target with project entry point
    # --------------------------------------------------------

    if startup_target and entry_point:
        entry_filename = os.path.basename(entry_point)

        diagnostics.append(
            f"Project entry file: {entry_filename}"
        )

        diagnostics.append(
            f"Startup target matches project entry file: "
            f"{startup_target == entry_filename}"
        )

    # --------------------------------------------------------
    # Check Dockerignore
    # --------------------------------------------------------

    ignored_files = {
        line.strip()
        for line in dockerignore.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    if startup_target:
        diagnostics.append(
            f"Startup target listed in .dockerignore: "
            f"{startup_target in ignored_files}"
        )

    if entry_point:
        entry_filename = os.path.basename(entry_point)

        diagnostics.append(
            f"Project entry file listed in .dockerignore: "
            f"{entry_filename in ignored_files}"
        )

    return "\n".join(diagnostics)


def is_docker_infrastructure_error(docker_result):
    build_error = docker_result.get("build_stderr", "")
    run_error = docker_result.get("run_stderr", "")

    combined_error = (
        build_error + "\n" + run_error
    ).lower()

    strong_infra_signals = [
        "connection refused",
        "connection reset",
        "network is unreachable",
        "could not resolve host",

        # Docker / BuildKit infrastructure failures
        # Keep these specific: generic Docker build errors
        # can be caused by a bad Dockerfile.
        "parent snapshot",
        "snapshot does not exist",
        "failed to prepare extraction snapshot",
        "connection to docker daemon failed",
        "cannot connect to the docker daemon",
        "is the docker daemon running",
    ]

    return any(
        signal in combined_error
        for signal in strong_infra_signals
    )


def validate_docker(project_path, project_info):
    """
    Build and run the project using Docker.

    Returns:
        docker_result: Raw Docker execution result
        debug_type: docker_build, docker_runtime,
                    docker_infrastructure, or docker_success
    """

    print("\n===== RUNNING DOCKER VALIDATION =====")

    docker_result = build_and_run_docker(
        project_path,
        entry_point=project_info["entry_point"],
        project_info=project_info
    )

    print("\n===== DOCKER IMAGE =====")
    print(docker_result.get("image_name", ""))

    print("\n===== DOCKER BUILD STDOUT =====")
    print(docker_result["build_stdout"])

    print("\n===== DOCKER BUILD STDERR =====")
    print(docker_result["build_stderr"])

    print("\n===== DOCKER BUILD RETURN CODE =====")
    print(docker_result["build_returncode"])

    print("\n===== DOCKER CONTAINER STDOUT =====")
    print(docker_result["run_stdout"])

    print("\n===== DOCKER CONTAINER STDERR =====")
    print(docker_result["run_stderr"])

    print("\n===== DOCKER CONTAINER RETURN CODE =====")
    print(docker_result["run_returncode"])

    if (
        docker_result["build_returncode"] == 0
        and docker_result["run_returncode"] == 0
    ):
        debug_type = "docker_success"

        print("\n✅ DOCKER VALIDATION PASSED")

        return docker_result, debug_type

    print("\n❌ DOCKER VALIDATION FAILED")

    if docker_result["build_returncode"] != 0:
        debug_type = "docker_build"
    else:
        debug_type = "docker_runtime"

    if is_docker_infrastructure_error(docker_result):
        print("\n⚠️ DETECTED EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
        print("This looks like a registry/network issue, not a project problem.")
        debug_type = "docker_infrastructure"

    print(
        f"\n===== DEBUG: CLASSIFIED FAILURE AS: "
        f"{debug_type} ====="
    )

    return docker_result, debug_type
