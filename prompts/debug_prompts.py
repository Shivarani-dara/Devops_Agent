def application_error_prompt(
    project_path,
    app_file,
    error,
    code,
    source_files,
    requirements_content,
    error_type="unknown",
    allowed_fix_files=None,
    failed_fix_info=""
):
        if allowed_fix_files is None:
           allowed_fix_files = []
        return f"""
You are a Python debugging agent.

Your task is to diagnose the ACTUAL application error and propose ONE
minimal source-code fix.

Do not guess.
Do not use examples from this prompt as source code.
For source-code fixes, CURRENT SOURCE CODE is the authority for the "old" field.

For requirements.txt fixes, CURRENT REQUIREMENTS FILE CONTENTS is the authority
for the "old" field.

==================================================
PROJECT
==================================================

Project:
{project_path}

Entry file:
{app_file}

Available source files:
{source_files}


Dependency/configuration files that may be modified when appropriate:
requirements.txt

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

For Python source-code fixes:
The "old" value MUST come directly from CURRENT SOURCE CODE.

For requirements.txt fixes:
The "old" value MUST come directly from CURRENT REQUIREMENTS FILE CONTENTS.

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
For Python source-code fixes, never return an empty "old" value.

For requirements.txt:
- If the current requirements.txt is empty, "old" may be "".
- If requirements.txt is not empty, "old" MUST contain its exact current contents.

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

NAMEERROR
==================================================

If the error is NameError:

1. Find the missing name.

2. Check whether it should be imported.

3. Check spelling.

4. Fix the actual source of the missing name.

Do not delete the line that uses the missing name.

==================================================
MODULENOTFOUNDERROR
==================================================

If the error is:

    ModuleNotFoundError: No module named 'X'

You MUST first determine whether X is genuinely used anywhere in
the current source code (an actual import that is referenced,
not a leftover unused import).

CURRENT REQUIREMENTS FILE CONTENTS:

{requirements_content}

Follow this decision process:

1. If X IS used in the source code, and X is MISSING from the
   requirements file above, the fix is to add X to
   requirements.txt. Do NOT modify app.py. Do NOT remove the
   import. Do NOT invent new application code, new classes, new
   app initialization, or any functionality that was not already
   present in the source.

   Example correct fix in this case:
   {{
       "file": "requirements.txt",
       "old": "<the exact current contents of requirements.txt>",
       "new": "<the exact current contents, plus X added>",
       "reason": "X is imported by the application but missing from requirements.txt"
   }}

2. If X is imported but NEVER actually used anywhere else in the
   source code (a genuinely unused import), the fix is to remove
   that one import line from the source file. Do NOT add X to
   requirements.txt in this case.

3. Never do both at once. Pick exactly one: add the dependency,
   OR remove the unused import — based on whether X is actually
   used in the code.
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

1. "file" is exactly one of:

{source_files}

or "requirements.txt" ONLY for dependency-related errors.

2. For Python source-code fixes:
   "old" MUST be copied exactly from CURRENT SOURCE CODE.

3. For requirements.txt fixes:
   "old" MUST be copied exactly from CURRENT REQUIREMENTS FILE CONTENTS.

4. For Python source-code fixes, "old" MUST NOT be empty.

5. For requirements.txt, "old" may be empty ONLY if
   CURRENT REQUIREMENTS FILE CONTENTS is completely empty.

6. "old" must be copied character-for-character.

7. "new" must contain only replacement content.

8. If file is a Python source file, "new" must be valid Python.

9. If file is requirements.txt, "new" must be valid requirements.txt content.

10. The fix must address the actual error.

11. The fix must be minimal.

12. No test must be modified.
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
    project_files = (
        project_info.get("files", [])
        if project_info
        else []
    )

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

def dockerignore_failure_prompt(
    error,
    dockerignore,
    docker_startup_diagnostics="",
    failed_fix_info=""
):
    return f"""
You are a DevOps debugging agent specializing in .dockerignore failures.

The deterministic Docker diagnostics have identified that the Docker
startup failure is caused by a file being excluded by .dockerignore.

Your task:
1. Identify the exact ignored entry responsible for the failure.
2. Propose ONE minimal change to .dockerignore.
3. Return ONLY valid JSON.

==================================================
CURRENT DOCKER ERROR
==================================================

{error}

==================================================
CURRENT DOCKERIGNORE
==================================================

{dockerignore}

==================================================
DETERMINISTIC DIAGNOSTICS
==================================================

{docker_startup_diagnostics}

Treat these diagnostics as factual evidence.

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

{failed_fix_info}

Previous attempts are historical only.
Do not copy old/new values from them.

==================================================
PATCH SEMANTICS
==================================================

The "old" value MUST be text that currently exists in the
CURRENT .dockerignore file.

The "new" value MUST be the exact replacement for "old".

If an existing ignored entry must be removed:

- "old" MUST contain the exact existing ignored entry.
- "new" MUST be an empty string.

For the current situation, CURRENT .dockerignore contains:

app.py

Therefore, if app.py is the entry causing the failure:

- old MUST be: app.py
- new MUST be empty

NEVER use an empty "old" value.

NEVER invent text that does not currently exist in .dockerignore.

NEVER add app.py back when app.py is already present and causing
the Docker startup failure.

The "old" value MUST be copied from CURRENT .dockerignore above.

Make exactly ONE minimal change.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON with these four fields:

file
old
new
reason

The file MUST be .dockerignore.
"""


def docker_failure_prompt(
    project_path,
    app_file,
    error,
    code,
    dockerfile,
    dockerignore,
    docker_startup_diagnostics="",
    project_info=None,
    failed_fix_info=""
):
    project_files = (
        project_info.get("files", [])
        if project_info
        else []
    )

    return f"""
You are an expert DevOps debugging agent.

Docker validation failed after the application and local tests passed.

Your task:
1. Identify the ACTUAL Docker root cause.
2. Propose ONE minimal project-file change.
3. Return ONLY valid JSON.

==================================================
CURRENT PROJECT
==================================================

Project:
{project_path}

Entry file:
{app_file}

Project information:
{project_info}

Project file inventory:
{project_files}

Use this inventory as factual evidence of which files currently
exist in the project. In particular, compare files referenced by
Dockerfile COPY/ADD instructions against this inventory.

==================================================
CURRENT DOCKER ERROR
==================================================

{error}

==================================================
CURRENT DOCKERFILE
==================================================

{dockerfile}

==================================================
CURRENT DOCKERIGNORE
==================================================

{dockerignore}

==================================================
DETERMINISTIC STARTUP DIAGNOSTICS
==================================================

{docker_startup_diagnostics}

These diagnostics were calculated from the CURRENT project.

Treat them as factual evidence.

They do NOT directly specify the fix.

Use them together with the CURRENT Dockerfile, CURRENT
.dockerignore, CURRENT error, and project information.

==================================================
CURRENT APPLICATION SOURCE
==================================================

{code}

==================================================
PREVIOUS FAILED ATTEMPTS
==================================================

{failed_fix_info}

Previous attempts are historical only.

NEVER copy an old/new value from previous attempts.

NEVER assume a file still contains text from a previous attempt.

==================================================
STRICT REASONING RULES
==================================================

Reason ONLY from the CURRENT project state.

Do NOT use examples, remembered values, or previous attempts
as evidence.

Do NOT invent file contents.

Do NOT modify application source code unless the Docker error
clearly proves that application source code is the root cause.

Determine which CURRENT project file actually owns the problem.

Possible files include:

- Dockerfile
- .dockerignore
- requirements.txt
- an application source file

==================================================
DOCKERFILE / DOCKERIGNORE DECISION
==================================================

For a container startup failure involving a missing file:

1. Identify the file referenced by the CURRENT Docker error.

2. Check the CURRENT Dockerfile CMD/ENTRYPOINT.

3. Check whether that startup target exists in the project.

4. Check whether the required file is excluded by the CURRENT
   .dockerignore.

5. Check WORKDIR and COPY/ADD instructions.

6. Determine which CURRENT configuration actually causes the
   failure.

If CMD/ENTRYPOINT is wrong, modify Dockerfile.

If CMD/ENTRYPOINT is correct AND the required startup file exists
in the project BUT is listed in .dockerignore, the .dockerignore
entry is the PRIMARY root cause. Modify .dockerignore to remove
that ignored file.

If the deterministic diagnostics explicitly report:

"Startup target listed in .dockerignore: True"

AND:

"Startup target exists in project: True"

AND the Docker error says that the startup target cannot be found
inside the container, you MUST select .dockerignore as the fix
target.

In this situation, DO NOT modify CMD, ENTRYPOINT, Python
interpreter, WORKDIR, or unrelated Dockerfile instructions.

If COPY/WORKDIR is responsible and the startup file is NOT excluded
by .dockerignore, modify Dockerfile.

Do NOT change CMD merely because a file is missing.

Do NOT change .dockerignore merely because Docker failed.

Use the CURRENT evidence to decide.

==================================================
EXTERNAL FAILURE
==================================================

If the failure is caused by external infrastructure such as:

- registry outage
- image pull failure
- proxy failure
- DNS failure
- network timeout
- authentication failure

do NOT invent a project-file fix.

Return:

{{
    "file": "",
    "old": "",
    "new": "",
    "reason": "External Docker infrastructure failure: explain the actual cause"
}}

==================================================
STRICT "old" RULE
==================================================

The "old" value MUST be copied EXACTLY from the CURRENT file
identified in "file".

Before returning JSON, verify:

CURRENT FILE contains OLD exactly.

If it does not, the proposed fix is INVALID.

Never use:

- previous attempt text
- hypothetical text
- example text
- Docker error text
- invented text

as "old".

Keep "old" minimal: preferably one exact line.

For .dockerignore, if removing one ignored file, "old" must be
the exact line that currently exists in the CURRENT .dockerignore
file, and "new" must be an empty string.

==================================================
GENERAL EDIT SEMANTICS
==================================================

The fix uses literal text replacement:

"old" = the exact text that CURRENTLY EXISTS in the selected file.

"new" = the exact text that should REPLACE "old".

If an existing line must be removed:

"old": "<exact existing line>"
"new": ""

If existing text must be changed:

"old": "<exact existing text>"
"new": "<replacement text>"

NEVER use an empty "old" value to represent deletion.

NEVER invent the "old" value.

The actual "old" and "new" values MUST be derived from the
CURRENT FILE CONTENT provided in this prompt.

==================================================
STRICT "new" RULE
==================================================

"new" must be the exact replacement for "old".

Make ONE minimal change.

Do not rewrite the entire file.

Do not modify tests.

Do not modify unrelated files.

==================================================
FINAL CHECK BEFORE JSON
==================================================

Verify all of these:

1. The diagnosis matches the CURRENT Docker error.
2. The selected file is actually responsible.
3. "old" literally exists in the CURRENT file.
4. "old" is copied character-for-character.
5. "new" is the minimal replacement.
6. No previous failed fix is being repeated.
7. No test is modified.
8. No unrelated file is modified.

==================================================
OUTPUT
==================================================

Return ONLY JSON.

For a project-file fix:

{{
    "file": "exact current filename",
    "old": "exact text copied from that current file",
    "new": "replacement text",
    "reason": "short explanation based only on current evidence"
}}

Return the JSON now.
"""
