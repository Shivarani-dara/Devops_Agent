from tools.docker_tools import build_and_run_docker


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
        "timeout",
        "temporary failure",
        "dns",
        "could not resolve host",
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
