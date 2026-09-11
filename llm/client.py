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
        """

        failed_command = diagnostics.get("failed_command")

        project_info = diagnostics.get("project_info", {})
        available_files = project_info.get("files", [])
        test_files = project_info.get("test_files", [])

        prompt = f"""
You are generating a minimal fix for a Jenkins CI/CD failure.

FAILED JENKINS COMMAND:
{failed_command}

AVAILABLE PROJECT FILES:
{available_files}

AVAILABLE TEST FILES:
{test_files}

COMPLETE JENKINS DIAGNOSTIC CONTEXT:
{diagnostics}

LLM DIAGNOSIS:
{diagnosis}

Your task:

1. Identify the Jenkins Pipeline stage that caused the failure.
2. The failed command is explicitly provided above.
3. Determine the smallest possible change that fixes the failure.
4. Use the project information as evidence.
5. Do NOT create new files.
6. Do NOT modify application source code unless the diagnosis proves it is the cause.
7. Do NOT modify unrelated Jenkins stages.
8. Do NOT change dependency installation commands when the failure is in the test stage.
9. "old" MUST be EXACTLY the value of FAILED JENKINS COMMAND above.
10. "new" MUST contain ONLY the corrected command.
11. Do NOT include shell output, Jenkins log prefixes, or error messages in "old" or "new".
12. NEVER invent a file, directory, or path.
13. Every file or directory referenced by "new" MUST be supported by the
    AVAILABLE PROJECT FILES or AVAILABLE TEST FILES.
14. If the failed pytest target does not exist, use the actual test directory
    or test file shown by the project scanner.
15. Prefer the smallest change that restores the existing project workflow.

For this project, the scanner reports:

Available test files:
{test_files}

Therefore, do not invent names such as:
- app_test.py
- nonexist.py
- test.py

Return ONLY valid JSON:

{{
    "target": "jenkins_pipeline",
    "stage": "...",
    "old": "{failed_command}",
    "new": "...",
    "reason": "..."
}}
"""

        response = ollama.chat(
            model=self.model,
            format={{
                "type": "object",
                "properties": {{
                    "target": {{"type": "string"}},
                    "stage": {{"type": "string"}},
                    "old": {{"type": "string"}},
                    "new": {{"type": "string"}},
                    "reason": {{"type": "string"}}
                }},
                "required": [
                    "target",
                    "stage",
                    "old",
                    "new",
                    "reason"
                ]
            }},
            messages=[
                {{
                    "role": "user",
                    "content": prompt
                }}
            ]
        )

        return response.message.content

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

        return response.message.content


    def generate_jenkins_fix(self, diagnostics, diagnosis):
        """
        Generate a minimal fix for a Jenkins Pipeline failure.
        """

        failed_command = diagnostics.get("failed_command")

        prompt = f"""
    You are generating a minimal fix for a Jenkins CI/CD failure.

    FAILED JENKINS COMMAND:
    {failed_command}

    COMPLETE JENKINS DIAGNOSTIC CONTEXT:
    {diagnostics}

    LLM DIAGNOSIS:
    {diagnosis}

    Your task:

    1. Identify the Jenkins Pipeline stage that caused the failure.
    2. The failed command is explicitly provided above.
    3. Determine the smallest possible change that fixes the failure.
    4. Use the project information as evidence.
    5. Do NOT create new files.
    6. Do NOT modify application source code unless the diagnosis proves it is the cause.
    7. Do NOT modify unrelated Jenkins stages.
    8. Do NOT change dependency installation commands when the failure is in the test stage.
    9. "old" MUST be EXACTLY the value of FAILED JENKINS COMMAND above.
    10. "new" MUST contain ONLY the corrected command.
    11. Do NOT include shell output, Jenkins log prefixes, or error messages in "old" or "new".
    12. Do NOT invent commands or file paths.

    Return ONLY valid JSON:

    {{
        "target": "jenkins_pipeline",
        "stage": "...",
        "old": "{failed_command}",
        "new": "...",
        "reason": "..."
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

        return response.message.content






        