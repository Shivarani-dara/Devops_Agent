import subprocess
import os



def ensure_dockerfile(project_path, project_info):
    """
    Create a standard Dockerfile automatically if the project
    does not already have one.

    Existing Dockerfiles are never overwritten.
    """

    dockerfile_path = os.path.join(
        project_path,
        "Dockerfile"
    )

    # --------------------------------------------------------
    # Dockerfile already exists
    # --------------------------------------------------------

    if os.path.exists(dockerfile_path):

        print("\n✅ Dockerfile already exists.")

        return {
            "success": True,
            "created": False,
            "path": dockerfile_path
        }

    # --------------------------------------------------------
    # Get project information
    # --------------------------------------------------------

    project_type = project_info.get("type")

    entry_point = project_info.get("entry_point")

    requirements_file = project_info.get(
        "requirements_file"
    )

    # --------------------------------------------------------
    # Currently support Python projects
    # --------------------------------------------------------

    if project_type != "python":

        return {
            "success": False,
            "created": False,
            "path": dockerfile_path,
            "error": (
                f"Automatic Dockerfile generation is currently "
                f"supported only for Python projects. "
                f"Detected project type: {project_type}"
            )
        }

    if not entry_point:

        return {
            "success": False,
            "created": False,
            "path": dockerfile_path,
            "error": "Could not determine Python entry point."
        }

    # --------------------------------------------------------
    # Build Dockerfile
    # --------------------------------------------------------

    dockerfile_lines = [
        "FROM python:3.10-slim",
        "",
        "WORKDIR /app",
        ""
    ]

    # --------------------------------------------------------
    # requirements.txt
    # --------------------------------------------------------

    if requirements_file:

        dockerfile_lines.extend([
            f"COPY {requirements_file} .",
            "",
            f"RUN pip install --no-cache-dir -r {requirements_file}",
            ""
        ])

    # --------------------------------------------------------
    # Copy project
    # --------------------------------------------------------

    dockerfile_lines.extend([
        "COPY . .",
        "",
        f'CMD ["python", "{entry_point}"]',
        ""
    ])

    dockerfile_content = "\n".join(
        dockerfile_lines
    )

    # --------------------------------------------------------
    # Write Dockerfile
    # --------------------------------------------------------

    try:

        with open(
            dockerfile_path,
            "w"
        ) as f:

            f.write(
                dockerfile_content
            )

    except Exception as e:

        return {
            "success": False,
            "created": False,
            "path": dockerfile_path,
            "error": str(e)
        }

    print("\n📝 Dockerfile was missing.")
    print("✅ Generated Dockerfile automatically.")

    print("\n===== GENERATED DOCKERFILE =====")
    print(dockerfile_content)
    print("================================")

    return {
        "success": True,
        "created": True,
        "path": dockerfile_path
    }


def build_and_run_docker(
    project_path,
    entry_point="app.py",
    project_info=None
):

        # =========================================================
    # ENSURE DOCKERFILE EXISTS
    # =========================================================

    if project_info is not None:

        dockerfile_result = ensure_dockerfile(
            project_path,
            project_info
        )

        if not dockerfile_result["success"]:

            return {
                "image_name": "",
                "build_stdout": "",
                "build_stderr": dockerfile_result["error"],
                "build_returncode": 1,
                "run_stdout": "",
                "run_stderr": "",
                "run_returncode": -1
            }

    

    
    project_path = os.path.abspath(project_path)

    # Get project name
    project_name = os.path.basename(project_path).lower()

    # Docker image name
    image_name = f"devops-agent-{project_name}:latest"

    # =========================
    # STEP 1: BUILD IMAGE
    # =========================

    print("===== DOCKER IMAGE BUILD =====")
    print(f"Image: {image_name}")

    build_result = subprocess.run(
        [
            "docker",
            "build",
            "-t",
            image_name,
            project_path
        ],
        capture_output=True,
        text=True
    )

    # If build failed, don't try to run the container
    if build_result.returncode != 0:
        return {
            "image_name": image_name,
            "build_stdout": build_result.stdout,
            "build_stderr": build_result.stderr,
            "build_returncode": build_result.returncode,
            "run_stdout": "",
            "run_stderr": "",
            "run_returncode": -1
        }

    print("✅ DOCKER IMAGE BUILT SUCCESSFULLY")

    # =========================
    # STEP 2: RUN APPLICATION
    # =========================

    print("===== DOCKER CONTAINER RUN =====")

    run_result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            image_name,
            "python",
            entry_point
        ],
        capture_output=True,
        text=True
    )

    return {
        "image_name": image_name,

        "build_stdout": build_result.stdout,
        "build_stderr": build_result.stderr,
        "build_returncode": build_result.returncode,

        "run_stdout": run_result.stdout,
        "run_stderr": run_result.stderr,
        "run_returncode": run_result.returncode
    }








if __name__ == "__main__":
    project_path = "/home/darashivarani/calculator"

    result = build_and_run_docker(
        project_path,
        entry_point="app.py"
    )

    print("\n===== BUILD STDOUT =====")
    print(result["build_stdout"])

    print("\n===== BUILD STDERR =====")
    print(result["build_stderr"])

    print("\n===== BUILD RETURN CODE =====")
    print(result["build_returncode"])

    print("\n===== IMAGE =====")
    print(result["image_name"])

    print("\n===== CONTAINER STDOUT =====")
    print(result["run_stdout"])

    print("\n===== CONTAINER STDERR =====")
    print(result["run_stderr"])

    print("\n===== CONTAINER RETURN CODE =====")
    print(result["run_returncode"])