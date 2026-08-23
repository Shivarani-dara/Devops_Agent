def application_error_prompt(
    project_path,
    app_file,
    error,
    code,
    source_files,
    failed_fix_info=""
):
    return f"""
You are a Python debugging agent.

Your task is to diagnose the ACTUAL application error and propose ONE
minimal source-code fix.

Do not guess.
Do not use examples from this prompt as source code.
The CURRENT SOURCE CODE below is the only authority for the "old" field.

==================================================
PROJECT
==================================================

Project:
{project_path}

Entry file:
{app_file}

Available source files:
{source_files}

==================================================
APPLICATION ERROR
==================================================

{error}

==================================================
CURRENT SOURCE CODE
==================================================

{code}

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

{failed_fix_info}

IMPORTANT:

Previous failed attempts refer to older attempts.

NEVER copy the "old" value from PREVIOUS FAILED ATTEMPTS.

The "old" value MUST come directly from CURRENT SOURCE CODE above.

==================================================
DEBUGGING PROCESS
==================================================

Follow this process:

1. Read the complete error.

2. Identify:
   - exception type
   - failing file
   - failing line
   - function
   - incorrect operation

3. Locate that code in CURRENT SOURCE CODE.

4. Determine the smallest change that fixes the actual problem.

5. Prefer changing one expression or one line.

6. Do not rewrite the function unless necessary.

7. Do not modify tests.

8. Do not suppress the exception.

9. Do not add unnecessary try/except blocks.

10. Do not change unrelated code.

11. If another source file contains the actual bug,
    modify that file instead of blindly modifying the entry file.

==================================================
CRITICAL RULE FOR "old"
==================================================

The "old" value is NOT a description.

It is NOT the traceback.

It is NOT an example.

It is NOT something remembered from a previous attempt.

It MUST be an EXACT substring copied from the CURRENT SOURCE CODE.

Before returning the answer, mentally perform:

    Does CURRENT SOURCE CODE literally contain my "old" value?

If the answer is NO, your answer is invalid.

Do not return an empty "old" value.

Do not invent an "old" value.

Do not change whitespace or indentation in "old".

Keep "old" as small as possible.

For example, if the current source contains:

    return a + b

then the old value may be:

    return a + b

But ONLY if that exact text actually appears in the current source.

Do not assume that code exists.
Look at CURRENT SOURCE CODE.

==================================================
CRITICAL RULE FOR "new"
==================================================

"new" must be the replacement for "old".

It must:

- be valid Python
- solve the actual error
- preserve intended behavior
- contain only source code
- contain no explanation
- contain no markdown

Do not hard-code a particular test case.

Do not change function behavior unnecessarily.

==================================================
TYPEERROR
==================================================

If the error is TypeError:

1. Identify the incompatible values.

2. Look at where those values come from.

3. Determine the intended operation.

4. Fix the actual source of the incompatible values.

Do not automatically add conversions such as int(), str(),
or isinstance() unless the source code and program behavior
justify that change.

==================================================
NAMEERROR
==================================================

If the error is NameError:

1. Find the missing name.

2. Check whether it should be imported.

3. Check spelling.

4. Fix the actual source of the missing name.

Do not delete the line that uses the missing name.

==================================================
INDEXERROR / KEYERROR
==================================================

Identify the invalid index or key.

Inspect how it was generated.

Fix the indexing/key logic.

Do not simply catch the exception.

==================================================
SYNTAXERROR / INDENTATIONERROR
==================================================

Inspect the affected source.

Fix only the invalid syntax or indentation.

Do not rewrite the entire file.

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

Previous failed attempts are only evidence that those proposed
changes were unsuccessful.

Do not repeat the same file/old/new combination.

Do not copy their "old" or "new" text.

Always inspect CURRENT SOURCE CODE again.

==================================================
FINAL VALIDATION
==================================================

Before returning the answer verify:

1. file is exactly one of:

{source_files}

2. old literally exists in CURRENT SOURCE CODE.

3. old was copied character-for-character.

4. old is not empty.

5. old contains only source code.

6. new contains only replacement source code.

7. new is valid Python.

8. the fix addresses the actual error.

9. the fix is minimal.

10. no test was modified.

==================================================
OUTPUT
==================================================

Return ONLY JSON.

No markdown.
No explanation outside JSON.

Use exactly:

{{
    "file": "filename.py",
    "old": "exact existing source code",
    "new": "replacement source code",
    "reason": "short explanation"
}}

Return the JSON now.
"""


def test_failure_prompt(
    project_path,
    app_file,
    error,
    code,
    test_info,
    source_files,
    failed_fix_info=""
):
    return f"""
You are a Python debugging agent.

The application runs, but automated tests are failing.

Your task is to determine why the tests fail and propose ONE minimal
source-code fix.

Do not modify the tests.

Do not guess.

The CURRENT SOURCE CODE is the only authority for the "old" field.

==================================================
PROJECT
==================================================

Project:
{project_path}

Entry file:
{app_file}

Available source files:
{source_files}

==================================================
TEST FAILURE
==================================================

{error}

==================================================
TEST INFORMATION
==================================================

{test_info}

==================================================
CURRENT SOURCE CODE
==================================================

{code}

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

{failed_fix_info}

IMPORTANT:

Previous failed attempts refer to older attempts.

NEVER copy their "old" or "new" values.

Only CURRENT SOURCE CODE may be used to construct "old".

==================================================
DEBUGGING PROCESS
==================================================

1. Read the failing test.

2. Determine exactly what behavior the test expects.

3. Locate the implementation responsible for that behavior.

4. Compare the expected behavior with the CURRENT SOURCE CODE.

5. Identify the actual incorrect expression or statement.

6. Change the smallest possible piece of code.

7. Preserve the general behavior of the function.

8. Do not modify tests.

9. Do not hard-code the expected test result.

10. Do not add unnecessary error handling.

11. Do not rewrite unrelated code.

12. If another source file contains the actual bug,
    modify that source file.

==================================================
CRITICAL "old" RULE
==================================================

The "old" value MUST be copied directly from CURRENT SOURCE CODE.

It must:

- literally exist in the current source
- preserve whitespace
- preserve indentation
- contain only source code
- contain no explanation
- contain no line numbers
- contain no traceback
- NOT be empty

Do not use:

- previous failed fixes
- test output
- traceback text
- remembered code
- hypothetical code

as the "old" value.

Before returning JSON, verify:

    CURRENT SOURCE CODE contains OLD

If it does not, choose a different exact piece of CURRENT SOURCE CODE.

==================================================
CRITICAL "new" RULE
==================================================

"new" must replace "old".

It must:

- be valid Python
- solve the failing test
- preserve intended general behavior
- contain only source code
- contain no markdown
- contain no explanation

Do not hard-code a single test case.

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

Previous attempts are only warnings.

Do not repeat the same failed file/old/new combination.

Do not copy their source text.

Re-analyze the CURRENT SOURCE CODE.

==================================================
FINAL CHECK
==================================================

Verify:

[ ] file is in AVAILABLE SOURCE FILES

[ ] old exists literally in CURRENT SOURCE CODE

[ ] old is copied exactly

[ ] old is not empty

[ ] new is valid Python

[ ] new fixes the actual test failure

[ ] tests are not modified

[ ] no unrelated code is changed

[ ] no previous failed fix is repeated

==================================================
OUTPUT
==================================================

Return ONLY JSON.

Use exactly:

{{
    "file": "filename.py",
    "old": "exact existing source code",
    "new": "replacement source code",
    "reason": "short explanation"
}}

Return the JSON now.
"""
def docker_failure_prompt(
    project_path,
    app_file,
    error,
    code,
    dockerfile,
    dockerignore,
    project_info,
    failed_fix_info=""
):
    return f"""
You are an expert DevOps debugging agent.

The application runs successfully and local automated tests pass,
but Docker validation has failed.

Your task is to diagnose the ACTUAL Docker failure and propose ONE
minimal fix.

IMPORTANT:
The failure may be caused by:

- Dockerfile configuration
- base image
- dependency installation
- COPY paths
- WORKDIR
- CMD or ENTRYPOINT
- environment variables
- exposed ports
- container startup command
- missing files
- Python/runtime configuration
- Docker build configuration

It may also be caused by an external infrastructure problem such as:

- Docker registry failure
- image pull failure
- proxy/network problem
- DNS problem
- authentication problem

Do NOT modify application source code unless the Docker error
clearly proves that the application code is responsible.

==================================================
PROJECT
==================================================

Project:
{project_path}

Entry file:
{app_file}

Project information:
{project_info}

==================================================
DOCKER FAILURE
==================================================

{error}

==================================================
DOCKERFILE
==================================================

{dockerfile}


==================================================
DOCKERIGNORE
==================================================

{dockerignore}

If a file the application needs (such as the entry point) is
listed in DOCKERIGNORE, that is very likely why the file is
missing inside the container. Consider removing that line from
.dockerignore as a possible fix, in addition to any Dockerfile fix.

==================================================
CURRENT APPLICATION SOURCE CODE
==================================================

{code}

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

{failed_fix_info}

IMPORTANT:

Previous failed attempts refer to older attempts.

NEVER copy their "old" or "new" values.

Only CURRENT SOURCE CODE or CURRENT DOCKERFILE may be used
when constructing the "old" value.

==================================================
DEBUGGING PROCESS
==================================================

Follow this process:

1. Read the complete Docker error.

2. Determine whether the failure happened during:

   - Docker image build
   - dependency installation
   - image creation
   - container startup
   - application execution inside container

3. Identify the exact failing command or Dockerfile instruction.


4. Determine the root cause.

5. Identify WHICH PROJECT FILE owns the failing instruction.

- If the error is "can't open file '<something>.py'" or a similar
  "file not found" error happening when the CONTAINER STARTS (not
  during the build), the CMD or ENTRYPOINT line is almost certainly
  running the WRONG FILENAME — not a wrong path, a wrong filename.

  The correct filename is the "Entry file" value shown in the
  PROJECT section above (currently: "{app_file}"). If CMD or
  ENTRYPOINT references any other filename, replace that filename
  with "{app_file}" exactly. Do NOT just add a directory path in
  front of the wrong filename — the filename itself is incorrect
  and must be replaced. Do NOT modify COPY instructions for this
  type of error.

- If the error occurs while installing Python dependencies and
  specifically identifies requirements.txt as the problem:
  MODIFY requirements.txt.

- If the Docker build succeeds but the application crashes
  inside the container because of application logic:
  MODIFY the appropriate application source file.

- NEVER modify application source code merely because it is
  available in the project.

6. For Dockerfile errors, inspect the CURRENT DOCKERFILE and
   find the exact instruction responsible for the error.

7. If the Dockerfile contains an invalid image tag, invalid
   instruction, incorrect path, incorrect command, or incorrect
   runtime configuration, modify the Dockerfile.

8. If the error is genuinely caused by external infrastructure
   such as a registry outage, proxy failure, DNS failure,
   network timeout, or authentication failure, DO NOT invent
   a project-file fix.

9. Make ONE minimal change.

10. Do not modify tests.

11. Do not rewrite the entire Dockerfile unnecessarily.

12. Do not modify unrelated files.


6. If the problem is an external infrastructure issue such as:

   - registry unavailable
   - proxy returning 403
   - network failure
   - DNS failure
   - authentication failure

   DO NOT invent a source-code fix.

7. If the Dockerfile is responsible, modify the Dockerfile.

8. If application source code is responsible, modify the
   appropriate source file.

9. Make ONE minimal change.

10. Do not modify tests.

11. Do not rewrite the entire Dockerfile unnecessarily.

12. Do not modify unrelated files.

==================================================
CRITICAL "old" RULE
==================================================

The "old" value MUST be copied directly from the CURRENT FILE
being modified.

The "old" value MUST be as SHORT as possible — ideally ONE line,
and NEVER more than 2-3 lines. Do NOT copy the entire file as
"old". Whole-file replacements almost always fail to match the
real file exactly and will be rejected. Pick the single specific
line that needs to change.

If the fix is to remove a line from .dockerignore, set "file" to
".dockerignore" and "old" to just that one line.

For example, if modifying the Dockerfile:

OLD:

FROM python:3.10-slim

then "old" must literally exist in the Dockerfile.

If modifying app.py:

OLD:

return a + b

then that exact code must exist in the current app.py.

Do NOT put the Docker error inside "old".

Do NOT put explanations inside "old".

Do NOT put line numbers inside "old".

Do NOT use code from previous failed attempts.

Do NOT invent an "old" value.

==================================================
EXTERNAL FAILURE RULE
==================================================

If the Docker failure is clearly caused by an external system
and there is no safe project-file change that can fix it,
return:

{{
    "file": "",
    "old": "",
    "new": "",
    "reason": "External Docker infrastructure failure: explain the actual cause"
}}

Examples include:

- 403 Forbidden from Docker registry
- registry unavailable
- DNS failure
- network timeout
- authentication failure

Do NOT change application code just to make an external
Docker failure disappear.

==================================================
OUTPUT FORMAT
==================================================

Return ONLY valid JSON.

If a project-file fix is required:

{{
    "file": "Dockerfile",
    "old": "exact existing source",
    "new": "replacement source",
    "reason": "short explanation"
}}

If application code must be changed:

{{
    "file": "app.py",
    "old": "exact existing source",
    "new": "replacement source",
    "reason": "short explanation"
}}

If the failure is external:

{{
    "file": "",
    "old": "",
    "new": "",
    "reason": "External Docker infrastructure failure: explain the actual cause"
}}

Return the JSON now.
"""
