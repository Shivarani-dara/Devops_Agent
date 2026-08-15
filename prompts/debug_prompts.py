def application_error_prompt(project_path, app_file, error, code):

    return f"""
You are a DevOps debugging agent.

PROJECT:
{project_path}

ENTRY FILE:
{app_file}

APPLICATION ERROR:
{error}

SOURCE CODE:
{code}

Analyze the application error and propose a safe minimal fix.

IMPORTANT RULES:

1. The file must be exactly:
{app_file}

2. The old value must be copied EXACTLY
   from the source code.

3. The old value must exist in the source code.

4. Do not reconstruct the old code.

5. Do not change indentation or spaces
   in the old value.

6. The new value must be valid Python.

7. Fix the actual error.

8. Do not suppress the error just to
   make the program exit successfully.

9. Do not modify unrelated code.

10. Return ONLY valid JSON.

Return:

{{
    "file": "{app_file}",
    "old": "exact code from source",
    "new": "replacement code",
    "reason": "explanation"
}}
"""

def test_failure_prompt(
    project_path,
    app_file,
    error,
    code,
    test_info
):

    return f"""
You are a DevOps debugging agent.

PROJECT:
{project_path}

ENTRY FILE:
{app_file}

The application runs successfully,
but automated tests are failing.

TEST FAILURE:
{error}

TEST INFORMATION:
{test_info}

SOURCE CODE:
{code}

Analyze the test failure and propose
a safe minimal fix.

The fix must satisfy the automated tests
while preserving the intended behavior.

IMPORTANT:

1. The file must be exactly:
{app_file}

2. The old value must be copied EXACTLY
   from the source code.

3. The old value must exist in the source code.

4. Do not reconstruct the old code.

5. The new value must be valid Python.

6. Do not modify unrelated code.

7. Do not simply suppress the failure.

8. Return ONLY valid JSON.

Return:

{{
    "file": "{app_file}",
    "old": "exact code from source",
    "new": "replacement code",
    "reason": "explanation"
}}
"""