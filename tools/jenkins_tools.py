from pathlib import Path
import xml.etree.ElementTree as ET
import os
import subprocess
import json
import time


def _jenkins_auth():
    """
    Get Jenkins credentials from environment variables.

    Credentials are never stored in this source file.
    """

    username = os.environ.get("JENKINS_USER")
    token = os.environ.get("JENKINS_TOKEN")

    if not username or not token:
        raise RuntimeError(
            "JENKINS_USER and JENKINS_TOKEN environment variables are required"
        )

    return username, token


def get_jenkins_build_log(
    job_name,
    build_number,
    jenkins_url="http://localhost:8080"
):
    """
    Retrieve the console log of a Jenkins build.
    """

    username, token = _jenkins_auth()

    url = (
        f"{jenkins_url.rstrip('/')}"
        f"/job/{job_name}/{build_number}/consoleText"
    )

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-u",
            f"{username}:{token}",
            url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "log": "",
            "error": result.stderr
        }

    return {
        "success": True,
        "log": result.stdout,
        "error": ""
    }


def get_jenkins_build_status(
    job_name,
    build_number,
    jenkins_url="http://localhost:8080"
):
    """
    Retrieve the status and metadata of a Jenkins build.
    """

    username, token = _jenkins_auth()

    url = (
        f"{jenkins_url.rstrip('/')}"
        f"/job/{job_name}/{build_number}/api/json"
    )

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-u",
            f"{username}:{token}",
            url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "status": None,
            "building": None,
            "build_number": build_number,
            "error": result.stderr
        }

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "status": None,
            "building": None,
            "build_number": build_number,
            "error": "Invalid JSON returned by Jenkins"
        }

    return {
        "success": True,
        "status": data.get("result"),
        "building": data.get("building"),
        "build_number": data.get("number"),
        "error": ""
    }





def trigger_jenkins_build(
    job_name,
    jenkins_url="http://localhost:8080",
    timeout=30
):
    """
    Trigger a Jenkins build and identify the exact build number
    created by this trigger.
    """

    username, token = _jenkins_auth()

    build_url = (
        f"{jenkins_url.rstrip('/')}"
        f"/job/{job_name}/build"
    )

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-i",
            "-X",
            "POST",
            "-u",
            f"{username}:{token}",
            build_url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "job_name": job_name,
            "queue_id": None,
            "build_number": None,
            "error": result.stderr
        }

    # Jenkins normally returns a Location header
    # pointing to the queue item.
    queue_url = None

    for line in result.stdout.splitlines():
        if line.lower().startswith("location:"):
            queue_url = line.split(":", 1)[1].strip()
            break

    if not queue_url:
        return {
            "success": False,
            "job_name": job_name,
            "queue_id": None,
            "build_number": None,
            "error": "Jenkins did not return a queue location"
        }

    # Example:
    # http://localhost:8080/queue/item/12/
    queue_id = queue_url.rstrip("/").split("/")[-1]

    queue_api_url = f"{queue_url.rstrip('/')}/api/json"

    start_time = time.time()

    while time.time() - start_time < timeout:

        queue_result = subprocess.run(
            [
                "curl",
                "-s",
                "-u",
                f"{username}:{token}",
                queue_api_url
            ],
            capture_output=True,
            text=True
        )

        if queue_result.returncode != 0:
            return {
                "success": False,
                "job_name": job_name,
                "queue_id": queue_id,
                "build_number": None,
                "error": queue_result.stderr
            }

        try:
            queue_data = json.loads(queue_result.stdout)
        except json.JSONDecodeError:
            return {
                "success": False,
                "job_name": job_name,
                "queue_id": queue_id,
                "build_number": None,
                "error": "Invalid JSON returned by Jenkins queue API"
            }

        executable = queue_data.get("executable")

        if executable:
            build_number = executable.get("number")

            return {
                "success": True,
                "job_name": job_name,
                "queue_id": queue_id,
                "build_number": build_number,
                "error": ""
            }

        if queue_data.get("cancelled"):
            return {
                "success": False,
                "job_name": job_name,
                "queue_id": queue_id,
                "build_number": None,
                "error": "Jenkins queue item was cancelled"
            }

        time.sleep(0.5)

    return {
        "success": False,
        "job_name": job_name,
        "queue_id": queue_id,
        "build_number": None,
        "error": "Timed out waiting for Jenkins to assign a build number"
    }

def get_jenkins_job_config(
    job_name,
    jenkins_url="http://localhost:8080"
):
    """
    Retrieve the Jenkins configuration for a job.

    For a Pipeline job, this can include the Pipeline script
    configured directly inside Jenkins.
    """

    username, token = _jenkins_auth()

    url = (
        f"{jenkins_url.rstrip('/')}"
        f"/job/{job_name}/config.xml"
    )

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-u",
            f"{username}:{token}",
            url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "job_name": job_name,
            "config": "",
            "error": result.stderr
        }

    if not result.stdout.strip():
        return {
            "success": False,
            "job_name": job_name,
            "config": "",
            "error": "Jenkins returned an empty job configuration"
        }

    return {
        "success": True,
        "job_name": job_name,
        "config": result.stdout,
        "error": ""
    }


def update_jenkins_job_config(
    job_name,
    old_command,
    new_command,
    jenkins_url="http://localhost:8080"
):
    """
    Safely update a Jenkins Pipeline configuration.

    Only the exact approved command inside the Pipeline script
    is modified. The rest of the Jenkins configuration remains
    unchanged.
    """

    import xml.etree.ElementTree as ET

    # ---------------------------------------------------------
    # 1. Get current Jenkins configuration
    # ---------------------------------------------------------

    config_result = get_jenkins_job_config(
        job_name,
        jenkins_url
    )

    if not config_result["success"]:
        return {
            "success": False,
            "job_name": job_name,
            "error": config_result["error"]
        }

    config_xml = config_result["config"]

    # ---------------------------------------------------------
    # 2. Parse Jenkins XML
    # ---------------------------------------------------------

    try:
        root = ET.fromstring(config_xml)
    except ET.ParseError as exc:
        return {
            "success": False,
            "job_name": job_name,
            "error": f"Invalid Jenkins configuration XML: {exc}"
        }

    # ---------------------------------------------------------
    # 3. Find the Pipeline script
    # ---------------------------------------------------------

    script_element = None

    for element in root.iter():
        if element.tag.endswith("script"):
            script_element = element
            break

    if script_element is None:
        return {
            "success": False,
            "job_name": job_name,
            "error": "Could not find Jenkins Pipeline script"
        }

    script = script_element.text or ""

    # ---------------------------------------------------------
    # 4. Verify the OLD command exists
    # ---------------------------------------------------------

    if old_command not in script:
        return {
            "success": False,
            "job_name": job_name,
            "error": (
                "The approved old command was not found "
                "inside the Jenkins Pipeline script"
            )
        }

    # ---------------------------------------------------------
    # 5. Prevent accidental multiple replacements
    # ---------------------------------------------------------

    occurrences = script.count(old_command)

    if occurrences != 1:
        return {
            "success": False,
            "job_name": job_name,
            "error": (
                f"Expected exactly one occurrence of the old "
                f"command, but found {occurrences}"
            )
        }

    # ---------------------------------------------------------
    # 6. Replace ONLY the approved command
    # ---------------------------------------------------------

    updated_script = script.replace(
        old_command,
        new_command,
        1
    )

    # ---------------------------------------------------------
    # 7. Put modified script back into XML
    # ---------------------------------------------------------

    script_element.text = updated_script

    # ---------------------------------------------------------
    # 8. Serialize XML
    # ---------------------------------------------------------

    updated_xml = ET.tostring(
        root,
        encoding="unicode"
    )

    # ---------------------------------------------------------
    # 9. Send updated configuration to Jenkins
    # ---------------------------------------------------------

    username, token = _jenkins_auth()

    url = (
        f"{jenkins_url.rstrip('/')}"
        f"/job/{job_name}/config.xml"
    )

    result = subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            "-u",
            f"{username}:{token}",
            "-H",
            "Content-Type: application/xml",
            "--data-binary",
            updated_xml,
            url
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "success": False,
            "job_name": job_name,
            "error": result.stderr
        }

    return {
        "success": True,
        "job_name": job_name,
        "old_command": old_command,
        "new_command": new_command,
        "error": ""
    }



def extract_jenkins_failed_command(log):
    """
    Extract the command that failed from a Jenkins console log.

    Jenkins shell commands normally appear as:
        + command

    The command is associated with failure messages appearing before
    the next shell command. This handles commands such as Docker builds
    where the error may appear many lines after the command.
    """

    lines = log.splitlines()

    failure_indicators = (
        "ERROR:",
        "error:",
        "Error:",
        "ERROR ",
        "script returned exit code",
        "failed to",
        "failed:",
        "FAILURE:",
        "BUILD FAILURE",
        "can't open file",
    )

    for i, line in enumerate(lines):

        line = line.strip()

        if not line.startswith("+ "):
            continue

        command = line[2:].strip()

        for next_line in lines[i + 1:]:

            stripped = next_line.strip()

            if stripped.startswith("+ "):
                break

            if any(
                indicator in stripped
                for indicator in failure_indicators
            ):
                return command

    return None


def collect_jenkins_diagnostics(
    job_name,
    build_number,
    project_path,
    jenkins_url="http://localhost:8080"
):
    """
    Collect the evidence needed to diagnose a Jenkins build failure.

    Jenkins Docker failures reuse the project's Docker infrastructure
    classification logic without running Docker a second time.
    """

    from project.scanner import scan_project
    from core.docker_validation import is_docker_infrastructure_error

    # ========================================================
    # 1. GET BUILD STATUS
    # ========================================================

    status_result = get_jenkins_build_status(
        job_name,
        build_number,
        jenkins_url
    )

    if not status_result["success"]:
        return {
            "success": False,
            "error": status_result["error"]
        }

    # ========================================================
    # 2. GET CONSOLE LOG
    # ========================================================

    log_result = get_jenkins_build_log(
        job_name,
        build_number,
        jenkins_url
    )

    if not log_result["success"]:
        return {
            "success": False,
            "error": log_result["error"]
        }

    console_log = log_result["log"]

    failed_command = extract_jenkins_failed_command(
        console_log
    )

    # ========================================================
    # 3. GET JENKINS JOB CONFIGURATION
    # ========================================================

    config_result = get_jenkins_job_config(
        job_name,
        jenkins_url
    )

    if not config_result["success"]:
        return {
            "success": False,
            "error": config_result["error"]
        }

    # ========================================================
    # 4. SCAN THE PROJECT
    # ========================================================

    project_info = scan_project(project_path)

    # ========================================================
    # 5. DOCKER-SPECIFIC JENKINS DIAGNOSTICS
    # ========================================================

    docker_diagnostics = {
        "detected": False,
        "debug_type": None,
        "infrastructure_failure": False,
        "evidence": ""
    }

    failed_command_lower = (
        failed_command or ""
    ).lower()

    console_lower = console_log.lower()

    is_docker_failure = (
        "docker build" in failed_command_lower
        or "docker run" in failed_command_lower
        or "docker build" in console_lower
        or "docker buildx" in console_lower
    )

    if is_docker_failure:

        docker_diagnostics["detected"] = True

        # Reuse the existing deterministic Docker
        # infrastructure classifier.
        docker_result = {
            "build_stderr": console_log,
            "run_stderr": ""
        }

        if is_docker_infrastructure_error(
            docker_result
        ):

            docker_diagnostics[
                "debug_type"
            ] = "docker_infrastructure"

            docker_diagnostics[
                "infrastructure_failure"
            ] = True

            docker_diagnostics[
                "evidence"
            ] = (
                "Jenkins Docker failure matches known "
                "Docker/BuildKit infrastructure signals."
            )

        else:

            if "docker run" in failed_command_lower:

                docker_diagnostics[
                    "debug_type"
                ] = "docker_runtime"

                docker_diagnostics[
                    "evidence"
                ] = (
                    "Jenkins Docker runtime command failed. "
                    "The Docker image was built successfully, "
                    "but the container execution failed."
                )

            else:

                docker_diagnostics[
                    "debug_type"
                ] = "docker_build"

                docker_diagnostics[
                    "evidence"
                ] = (
                    "Jenkins Docker build command failed. "
                    "The failure occurred during image construction."
                )

    # ========================================================
    # 6. RETURN COMPLETE DIAGNOSTICS
    # ========================================================

    return {
        "success": True,

        "job_name": job_name,
        "build_number": build_number,

        "status": status_result["status"],
        "building": status_result["building"],

        "console_log": console_log,
        "failed_command": failed_command,

        "jenkins_config": config_result["config"],

        "project_info": project_info,

        "docker_diagnostics": docker_diagnostics,

        "error": ""
    }


def wait_for_jenkins_build(
    job_name,
    build_number,
    jenkins_url="http://localhost:8080",
    poll_interval=3,
    timeout=300
):
    """
    Wait for a Jenkins build to finish.

    Returns the final Jenkins build status.
    """

    import time

    start_time = time.time()

    while True:

        # Check timeout
        if time.time() - start_time > timeout:
            return {
                "success": False,
                "job_name": job_name,
                "build_number": build_number,
                "status": None,
                "error": "Timed out waiting for Jenkins build"
            }

        status_result = get_jenkins_build_status(
            job_name,
            build_number,
            jenkins_url
        )

        if not status_result["success"]:
            return {
                "success": False,
                "job_name": job_name,
                "build_number": build_number,
                "status": None,
                "error": status_result["error"]
            }

        # Build is still running
        if status_result["building"]:
            time.sleep(poll_interval)
            continue

        # Build has finished
        return {
            "success": True,
            "job_name": job_name,
            "build_number": build_number,
            "status": status_result["status"],
            "error": ""
        }


def update_jenkinsfile(
    jenkinsfile_path,
    old_command,
    new_command,
):
    """
    Replace an exact Jenkins Pipeline command inside a Jenkinsfile.
    Does not commit or push the change.
    """

    path = Path(jenkinsfile_path)

    if not path.exists():
        return {
            "success": False,
            "error": f"Jenkinsfile not found: {jenkinsfile_path}",
        }

    content = path.read_text()

    if old_command not in content:
        return {
            "success": False,
            "error": (
                "The old command does not exist in the Jenkinsfile: "
                f"{old_command}"
            ),
        }

    if old_command == new_command:
        return {
            "success": False,
            "error": "Old and new Jenkins commands are identical.",
        }

    updated_content = content.replace(
        old_command,
        new_command,
        1,
    )

    path.write_text(updated_content)

    return {
        "success": True,
        "path": str(path),
        "old": old_command,
        "new": new_command,
        "error": "",
    }


def set_jenkins_pipeline_from_scm(
    job_name,
    repository_url,
    branch,
    script_path,
    jenkins_url="http://localhost:8080",
):
    """
    Configure a Jenkins Pipeline job to load its Jenkinsfile from Git SCM.
    """

    import xml.etree.ElementTree as ET
    import subprocess

    username, token = _jenkins_auth()

    config_result = get_jenkins_job_config(
        job_name,
        jenkins_url=jenkins_url,
    )

    if not config_result["success"]:
        return config_result

    try:
        root = ET.fromstring(config_result["config"])
        definition = root.find("./definition")

        if definition is None:
            return {
                "success": False,
                "error": "Pipeline definition not found in Jenkins job config.",
            }

        current_class = definition.attrib.get("class")

        if current_class not in {
            "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition",
            "org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition",
        }:
            return {
                "success": False,
                "error": (
                    "Unexpected Pipeline definition type: "
                    f"{current_class}"
                ),
            }

        # Change inline Pipeline definition to SCM Pipeline definition.
        definition.attrib["class"] = (
            "org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition"
        )

        # Remove inline script and sandbox settings.
        for child in list(definition):
            if child.tag in {"script", "sandbox"}:
                definition.remove(child)

        # Remove any existing SCM definition.
        for child in list(definition):
            if child.tag == "scm":
                definition.remove(child)

        # Build Git SCM configuration.
        scm = ET.Element(
            "scm",
            {
                "class": "hudson.plugins.git.GitSCM",
                "plugin": "git",
            },
        )

        ET.SubElement(scm, "configVersion").text = "2"

        user_remote_configs = ET.SubElement(
            scm,
            "userRemoteConfigs",
        )

        remote = ET.SubElement(
            user_remote_configs,
            "hudson.plugins.git.UserRemoteConfig",
        )

        ET.SubElement(remote, "url").text = repository_url

        branches = ET.SubElement(scm, "branches")

        branch_spec = ET.SubElement(
            branches,
            "hudson.plugins.git.BranchSpec",
        )

        ET.SubElement(branch_spec, "name").text = branch

        definition.insert(0, scm)

        # Jenkinsfile path.
        script_path_element = definition.find("scriptPath")

        if script_path_element is None:
            script_path_element = ET.SubElement(
                definition,
                "scriptPath",
            )

        script_path_element.text = script_path

        # Lightweight checkout.
        lightweight = definition.find("lightweight")

        if lightweight is None:
            lightweight = ET.SubElement(
                definition,
                "lightweight",
            )

        lightweight.text = "true"

        new_config = ET.tostring(
            root,
            encoding="unicode",
        )

        # Send configuration using curl, consistent with the rest
        # of the Jenkins tools.
        command = [
            "curl",
            "-sS",
            "-X",
            "POST",
            f"{jenkins_url}/job/{job_name}/config.xml",
            "-u",
            f"{username}:{token}",
            "-H",
            "Content-Type: application/xml",
            "--data-binary",
            "@-",
        ]

        result = subprocess.run(
            command,
            input=new_config,
            text=True,
            capture_output=True,
            timeout=30,
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": (
                    "Failed to update Jenkins configuration: "
                    f"{result.stderr.strip()}"
                ),
            }

        return {
            "success": True,
            "job_name": job_name,
            "repository_url": repository_url,
            "branch": branch,
            "script_path": script_path,
            "error": "",
        }

    except ET.ParseError as exc:
        return {
            "success": False,
            "error": f"Invalid Jenkins config XML: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to configure Jenkins SCM pipeline: {exc}",
        }

