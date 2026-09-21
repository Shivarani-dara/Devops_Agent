import json
import ollama


class LLMClient:

    def __init__(self, model="qwen2.5-coder:3b"):
        self.model = model

    def generate_fix(self, prompt):

        response = ollama.chat(

            model=self.model,

            format={
                "type": "object",

                "properties": {

                    "file": {
                        "type": "string"
                    },

                    "old": {
                        "type": "string"
                    },

                    "new": {
                        "type": "string"
                    },

                    "reason": {
                        "type": "string"
                    }
                },

                "required": [
                    "file",
                    "old",
                    "new",
                    "reason"
                ]
            },

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.message.content



    def generate_jenkins_diagnosis(self, job_name, build_number, log):
        """
        Analyze a Jenkins build failure and return a structured diagnosis.
        """

        prompt = f"""
You are debugging a Jenkins CI/CD failure.

Jenkins job: {job_name}
Build number: {build_number}

Jenkins console log:
--------------------
{log}
--------------------

Analyze the failure and determine:

1. What actually failed?
2. What is the likely root cause?
3. What evidence in the log supports your conclusion?
4. What category does the failure belong to?

Choose the failure category from:
- application
- test
- dependency
- docker
- ci_pipeline
- infrastructure
- unknown

Return ONLY valid JSON with this structure:

{{
    "failure_type": "...",
    "summary": "...",
    "root_cause": "...",
    "evidence": "...",
    "recommended_action": "..."
}}
"""

        response = ollama.chat(
            model=self.model,
            format={
                "type": "object",
                "properties": {
                    "failure_type": {"type": "string"},
                    "summary": {"type": "string"},
                    "root_cause": {"type": "string"},
                    "evidence": {"type": "string"},
                    "recommended_action": {"type": "string"}
                },
                "required": [
                    "failure_type",
                    "summary",
                    "root_cause",
                    "evidence",
                    "recommended_action"
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.message.content



    def generate_jenkins_fix(self, diagnostics, diagnosis):
        """
        Generate a minimal fix for a Jenkins Pipeline failure.

        The LLM receives the actual project files discovered by the scanner.
        It must select a valid repository-relative path from that information.
        """

        failed_command = diagnostics.get("failed_command") or diagnosis.get("failed_command")

        if failed_command:
            failed_command = failed_command.strip()
            if failed_command.startswith("+ "):
                failed_command = failed_command[2:].strip()

        project_info = diagnostics.get("project_info", {})

        available_files = project_info.get("files", [])
        test_files = project_info.get("test_files", [])
        jenkinsfile = project_info.get("jenkinsfile", "")

        prompt = f"""
You are generating a minimal fix for a Jenkins CI/CD failure.

JENKINSFILE:
{jenkinsfile}

FAILED JENKINS COMMAND:
{failed_command}

AVAILABLE PROJECT FILES DISCOVERED BY THE SCANNER:
{available_files}

AVAILABLE TEST FILES DISCOVERED BY THE SCANNER:
{test_files}

COMPLETE JENKINS DIAGNOSTIC CONTEXT:
{diagnostics}

LLM DIAGNOSIS:
{diagnosis}

Your task is to propose the smallest safe change that fixes the Jenkins failure.

Rules:

1. Identify the Jenkins stage that failed.
2. "old" MUST be exactly the failed Jenkins command shown above.
3. "new" MUST contain ONLY the corrected shell command.
4. Do NOT invent files, directories, filenames, or paths.
5. Every path referenced by "new" MUST exist in the scanner's AVAILABLE PROJECT FILES
   or AVAILABLE TEST FILES.
6. Treat the scanner's file lists as the source of truth for repository paths.
7. Do NOT infer a project directory prefix from the filesystem path.
8. Do NOT use absolute filesystem paths.
9. Jenkins commands must use repository-relative paths.
10. If the failure is caused by a nonexistent pytest target, select an existing
    test file or test directory from AVAILABLE TEST FILES.
11. Do NOT create new files.
12. Do NOT modify application source code unless the diagnosis proves that
    application source code caused the failure.
13. Do NOT modify unrelated Jenkins stages.
14. Prefer the smallest possible change.
15. Do not copy paths from the Jenkins error if the scanner proves that the path
    does not exist.
16. Do not assume a directory name that is not present in the scanner file list.

Return ONLY valid JSON in this exact structure:

{{
    "target": "jenkins_pipeline",
    "stage": "failed stage name",
    "old": "exact failed command",
    "new": "corrected command",
    "reason": "brief explanation"
}}
"""

        response = ollama.chat(
            model=self.model,
            format={
                "type": "object",
                "properties": {
                    "target": {"type": "string"},
                    "stage": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": [
                    "target",
                    "stage",
                    "old",
                    "new",
                    "reason"
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:
            fix = json.loads(response.message.content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by Jenkins fix generator: {exc}"
            )

        if not isinstance(fix, dict):
            raise ValueError("Jenkins fix generator did not return a JSON object.")

        return fix

    def generate_docker_fix(self, diagnostics, diagnosis):
        """
        Generate a minimal fix for a project-caused Docker failure.
        """

        from prompts.debug_prompts import docker_failure_prompt

        project_info = diagnostics.get("project_info", {})
        project_path = diagnostics.get("project_path", "")
        app_file = project_info.get("entry_point", "")

        error = diagnostics.get(
            "docker_error",
            diagnostics.get("console_log", "")
        )

        dockerfile_path = project_info.get("dockerfile", "Dockerfile")
        dockerignore_path = project_info.get("dockerignore", ".dockerignore")

        dockerfile = ""
        dockerignore = ""

        dockerfile_full_path = os.path.join(
            project_path,
            dockerfile_path
        )

        if os.path.exists(dockerfile_full_path):
            dockerfile = read_file(dockerfile_full_path)

        dockerignore_full_path = os.path.join(
            project_path,
            dockerignore_path
        )

        if os.path.exists(dockerignore_full_path):
            dockerignore = read_file(dockerignore_full_path)

        source_code = ""

        for source_file in project_info.get("source_files", []):
            source_path = os.path.join(
                project_path,
                source_file
            )

            if os.path.exists(source_path):
                source_code += (
                    f"\n===== FILE: {source_file} =====\n"
                    + read_file(source_path)
                )

        docker_diagnostics = diagnostics.get(
            "docker_diagnostics",
            {}
        )

        startup_diagnostics = docker_diagnostics.get(
            "startup_diagnostics",
            ""
        )

        prompt = docker_failure_prompt(
            project_path=project_path,
            app_file=app_file,
            error=error,
            code=source_code,
            dockerfile=dockerfile,
            dockerignore=dockerignore,
            docker_startup_diagnostics=startup_diagnostics,
            project_info=project_info,
            failed_fix_info=""
        )

        response = ollama.chat(
            model=self.model,
            format={
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": [
                    "file",
                    "old",
                    "new",
                    "reason"
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:
            fix = json.loads(response.message.content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by Docker fix generator: {exc}"
            )

        if not isinstance(fix, dict):
            raise ValueError(
                "Docker fix generator did not return a JSON object."
            )

        return fix

    def generate_jenkins_diagnosis_from_context(self, diagnostics):
        """
        Analyze a complete Jenkins diagnostic context.
        """

        prompt = f"""
    You are debugging a Jenkins CI/CD failure.

    Here is the complete diagnostic context:

    {diagnostics}

    Analyze the failure using ALL available evidence.

    Determine:

    1. Which Jenkins stage failed?
    2. What exact command failed?
    3. What is the root cause?
    4. What evidence proves the root cause?
    5. What category does the failure belong to?

    Choose the failure category from:
    - application
    - test
    - dependency
    - docker
    - ci_pipeline
    - infrastructure
    - unknown

    Do not guess.
    Use the Jenkins console log and project information as evidence.

    IMPORTANT DOCKER RULE:
    If docker_diagnostics["infrastructure_failure"] is true,
    classify the failure as infrastructure.
    Do NOT propose a Dockerfile, application, test, or dependency fix
    for a Docker/BuildKit infrastructure failure.
    Explain that the Jenkins/Docker environment must be repaired first.

    If infrastructure_failure is false, Docker failures may require
    normal project/Dockerfile diagnosis using the scanned project files.

    Return ONLY valid JSON:

    {{
        "failure_type": "...",
        "stage": "...",
        "failed_command": "...",
        "summary": "...",
        "root_cause": "...",
        "evidence": "...",
        "recommended_action": "..."
    }}
    """

        response = ollama.chat(
            model=self.model,
            format={
                "type": "object",
                "properties": {
                    "failure_type": {"type": "string"},
                    "stage": {"type": "string"},
                    "failed_command": {"type": "string"},
                    "summary": {"type": "string"},
                    "root_cause": {"type": "string"},
                    "evidence": {"type": "string"},
                    "recommended_action": {"type": "string"}
                },
                "required": [
                    "failure_type",
                    "stage",
                    "failed_command",
                    "summary",
                    "root_cause",
                    "evidence",
                    "recommended_action"
                ]
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:
            return json.loads(response.message.content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON returned by Jenkins diagnosis generator: {exc}"
            )


