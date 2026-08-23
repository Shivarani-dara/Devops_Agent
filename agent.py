import ollama
import json
import sys
import os

from tools.file_tools import read_file, modify_file
from core.validator import (validate_python_fix,validate_dockerfile_fix,validate_dockerignore_fix)

from project.scanner import scan_project
from project.runner import run_project

from tools.test_tools import run_tests
from tools.docker_tools import (build_and_run_docker,ensure_dockerfile)

from prompts.debug_prompts import (
    application_error_prompt,
    test_failure_prompt,docker_failure_prompt
)

from tools.git_tools import (
    git_checkpoint,
    git_rollback,
    git_commit_success
)

import re

def count_failed_tests(test_stdout):
    match = re.search(r'(\d+) failed', test_stdout)
    if match:
        return int(match.group(1))
    return 0


def is_docker_infrastructure_error(docker_result):
    build_error = docker_result.get("build_stderr", "")
    run_error = docker_result.get("run_stderr", "")

    combined_error = (
        build_error + "\n" + run_error
    ).lower()

    # Signals that strongly suggest a REAL infrastructure/network
    # problem — NOT just "this image tag doesn't exist".
    #
    # NOTE: "403 forbidden", "docker.io", and "mirror.gcr.io" were
    # intentionally removed. They appear on both genuine outages AND
    # ordinary invalid-tag errors (every tag resolution attempt
    # touches docker.io/mirror.gcr.io and can 403 either way), so
    # they can't reliably distinguish the two cases.
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


def build_test_info(project_path, project_info, test_result):
    test_source = ""
    for tf in project_info.get("test_files", []):
        tf_path = os.path.join(project_path, tf)
        tf_content = read_file(tf_path)
        test_source += f"\n===== TEST FILE: {tf} =====\n{tf_content}\n"
    return f"""
AUTOMATED TEST INFORMATION:
Test framework:
{project_info.get("test_framework")}
Test stdout:
{test_result["stdout"]}
Test stderr:
{test_result["stderr"]}
Test return code:
{test_result["returncode"]}
================ TEST SOURCE CODE ================
{test_source}
"""

def is_repeated_fix(candidate_fix, failed_fixes):
    """
    Returns True if a fix with the same file/old/new was already
    attempted and failed. Whitespace at the edges is ignored so
    near-identical retries still get caught.
    """
    for failed in failed_fixes:
        if (
            candidate_fix["file"] == failed["file"]
            and candidate_fix["old"].strip() == failed["old"].strip()
            and candidate_fix["new"].strip() == failed["new"].strip()
        ):
            return True

    return False

MAX_ATTEMPTS = 5


# ============================================================
# CHECK COMMAND LINE ARGUMENT
# ============================================================

if len(sys.argv) != 2:

    print("Usage: python3 agent.py <project_path>")
    sys.exit(1)


project_path = sys.argv[1]


# ============================================================
# CHECK PROJECT EXISTS
# ============================================================

if not os.path.isdir(project_path):

    print(f"ERROR: Project directory not found: {project_path}")
    sys.exit(1)


# ============================================================
# SCAN PROJECT
# ============================================================

project_info = scan_project(project_path)


print("\n===== PROJECT INFORMATION =====")

for key, value in project_info.items():

    print(f"{key}: {value}")


# ============================================================
# FIND ENTRY FILE
# ============================================================

entry_point = project_info.get("entry_point")


if not entry_point:

    print("\n❌ Could not find project entry point.")
    sys.exit(1)


app_file = os.path.join(
    project_path,
    entry_point
)


# ============================================================
# ERROR STATE
# ============================================================

error = ""

test_info = ""

last_error = ""

stored_debug_type = None

last_failed_count = float("inf") 

failed_fixes = []


# ============================================================
# MAIN AGENT LOOP
# ============================================================

attempt = 0

extra_instructions = ""


while attempt < MAX_ATTEMPTS:

    

    attempt += 1


    print("\n==============================")
    print(f"       ATTEMPT {attempt}")
    print("==============================")

    debug_type = stored_debug_type if stored_debug_type else "application"


    # ========================================================
    # RUN PROJECT
    # ========================================================

    if not error:

        result = run_project(project_info)


        # ----------------------------------------------------
        # APPLICATION FAILED
        # ----------------------------------------------------

        if result["returncode"] != 0:

            print("\n=== APPLICATION ERROR ===")
            print(result["stderr"])

            error = result["stderr"]

            last_error = result["stderr"]


        # ----------------------------------------------------
        # APPLICATION SUCCESSFUL
        # ----------------------------------------------------

        else:

            print("\n✅ APPLICATION RUNS SUCCESSFULLY")

            print("\nAPPLICATION OUTPUT:")
            print(result["stdout"])


            # =================================================
            # RUN TESTS
            # =================================================

            if project_info.get("test_framework"):

                print("\n===== RUNNING TESTS =====")


                test_result = run_tests(project_path)


                print("\n===== TEST OUTPUT =====")
                print(test_result["stdout"])


                if test_result["stderr"]:

                    print("\n===== TEST ERROR =====")
                    print(test_result["stderr"])


                print("\n===== TEST RETURN CODE =====")
                print(test_result["returncode"])


                # ------------------------------------------------
                # TESTS PASS
                # ------------------------------------------------
                if test_result["returncode"] == 0:
                    print("\n✅ ALL TESTS PASSED")
                    # =================================================
                    # DOCKER VALIDATION (runs BEFORE commit — commit
                    # only happens if Docker also passes, below)
                    # =================================================
                    # =================================================
                    # DOCKER VALIDATION
                    # =================================================

                    print("\n===== PREPARING DOCKER VALIDATION =====")


        

                     # =================================================
                    # DOCKER VALIDATION
                    # ================================================



                                                    

                    print("\n===== RUNNING DOCKER VALIDATION =====")

                    docker_result = build_and_run_docker(
                        project_path,
                        entry_point=project_info["entry_point"],
                        project_info=project_info
                    )

                    print("\n===== DOCKER IMAGE =====")
                    print(docker_result["image_name"])

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


                    # =================================================
                    # DOCKER PASSED
                    # =================================================

                    if (
                        docker_result["build_returncode"] == 0
                        and docker_result["run_returncode"] == 0
                    ):

                        print("\n✅ DOCKER VALIDATION PASSED")

                        # =============================================
                        # COMMIT SUCCESSFUL FIX
                        # =============================================

                        print("\n===== COMMITTING SUCCESSFUL FIX =====")

                        commit_result = git_commit_success(
                            project_path
                        )

                        if not commit_result["success"]:

                            print("\n❌ Could not commit successful fix.")
                            print(commit_result["stderr"])

                            break

                        print("✅ Successful fix committed.")

                        print("\n🎉 PROJECT SUCCESSFUL")

                        break


                    # =================================================
                    # DOCKER FAILED
                    # =================================================

                    else:

                        print("\n❌ DOCKER VALIDATION FAILED")

                        if docker_result["build_returncode"] != 0:
                            debug_type = "docker_build"
                        else:
                            debug_type = "docker_runtime"

                        stored_debug_type = debug_type

                        print(f"\n===== DEBUG: CLASSIFIED FAILURE AS: {debug_type} =====")


                        if is_docker_infrastructure_error(docker_result):
                            print("\n⚠️ DETECTED EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
                            print("This looks like a registry/network issue, not a project problem.")
                            debug_type = "docker_infrastructure"
                            stored_debug_type = debug_type


                        error = (
                            "The application and local tests passed, "
                            "but Docker validation failed.\n\n"

                            "DOCKER BUILD STDOUT:\n"
                            + docker_result["build_stdout"]

                            + "\n\nDOCKER BUILD STDERR:\n"
                            + docker_result["build_stderr"]

                            + "\n\nDOCKER BUILD RETURN CODE:\n"
                            + str(docker_result["build_returncode"])

                            + "\n\nDOCKER CONTAINER STDOUT:\n"
                            + docker_result["run_stdout"]

                            + "\n\nDOCKER CONTAINER STDERR:\n"
                            + docker_result["run_stderr"]

                            + "\n\nDOCKER CONTAINER RETURN CODE:\n"
                            + str(docker_result["run_returncode"])
                        )

                        test_info = build_test_info(
                            project_path,
                            project_info,
                            test_result
                        )

                        # =============================================
                        # NO AI FIX EXISTS YET — this is the pre-fix
                        # (first-run) Docker check, so there is no
                        # checkpoint to roll back to and no 'fix' to
                        # log. Just store the error, same as the
                        # sibling "tests fail" branch above.
                        # =============================================

                        print(
                            "\n🔄 Docker failure stored."
                        )

                        print(
                            "AI will analyze the Docker failure "
                            "on the next attempt."
                        )

                        if attempt == MAX_ATTEMPTS:

                            print(
                                "\n❌ Maximum attempts reached."
                            )

                            break

                        continue
                # ------------------------------------------------
                # TESTS FAIL
                # ------------------------------------------------

                else:

                    print("\n❌ TESTS FAILED")


                    # =================================================
                    # THIS IS THE IMPORTANT PART
                    #
                    # At this point there is NO newly applied fix.
                    #
                    # This can happen on the FIRST run.
                    #
                    # Therefore we DO NOT rollback here.
                    #
                    # We simply store the test failure and ask AI
                    # for a fix.
                    # =================================================


                    error = (
                        "The application runs successfully, "
                        "but the automated tests are failing.\n\n"

                        "TEST OUTPUT:\n"
                        + test_result["stdout"]

                        + "\n\nTEST ERROR:\n"
                        + test_result["stderr"]
                    )


                    test_info = build_test_info(project_path, project_info, test_result)


                    # Establish the real baseline failing-test count now,
                    # before any AI fix has been proposed. Without this,
                    # last_failed_count stays at infinity and the first
                    # post-fix test-failure count always looks like
                    # "progress" even when the fix made things worse.
                    last_failed_count = count_failed_tests(test_result["stdout"])


                    print("\n🔄 Test failure stored.")

                    print(
                        "AI will analyze the test failure "
                        "on the next attempt."
                    )


                    if attempt == MAX_ATTEMPTS:

                        print(
                            "\n❌ Maximum attempts reached."
                        )

                        break


                    continue


            # ------------------------------------------------
            # NO TEST FRAMEWORK
            # ------------------------------------------------

            else:

                print("\n⚠️ No test framework detected.")

                print("\n===== RUNNING DOCKER VALIDATION =====")


                docker_result = build_and_run_docker(
                    project_path,
                    entry_point=project_info["entry_point"],
                    project_info=project_info
                )


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

                    print("\n✅ DOCKER VALIDATION PASSED")


                    print(
                        "\n===== COMMITTING SUCCESSFUL FIX ====="
                    )


                    commit_result = git_commit_success(
                        project_path
                    )


                    if not commit_result["success"]:

                        print(
                            "\n❌ Could not commit successful fix."
                        )

                        print(commit_result["stderr"])

                        break


                    print("✅ Successful fix committed.")

                    print("\n🎉 PROJECT SUCCESSFUL")

                    break


                else:

                    print("\n❌ DOCKER VALIDATION FAILED")

                    if docker_result["build_returncode"] != 0:
                        debug_type = "docker_build"
                    else:
                        debug_type = "docker_runtime"

                    stored_debug_type = debug_type
                    
                    print(f"\n===== DEBUG: CLASSIFIED FAILURE AS: {debug_type} =====")

                    if is_docker_infrastructure_error(docker_result):
                            print("\n⚠️ DETECTED EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
                            print("This looks like a registry/network issue, not a project problem.")
                            debug_type = "docker_infrastructure"
                            stored_debug_type = debug_type

        


                    error = (
                        "The application passed locally, "
                        "but failed inside Docker.\n\n"

                        "DOCKER BUILD STDOUT:\n"
                        + docker_result["build_stdout"]

                        + "\n\nDOCKER BUILD STDERR:\n"
                        + docker_result["build_stderr"]

                        + "\n\nDOCKER CONTAINER STDOUT:\n"
                        + docker_result["run_stdout"]

                        + "\n\nDOCKER CONTAINER STDERR:\n"
                        + docker_result["run_stderr"]
                    )


                    # =============================================
                    # NO AI FIX EXISTS YET — this is the pre-fix
                    # (first-run) Docker check, so there is no
                    # checkpoint to roll back to and no 'fix' to
                    # log. Just store the error and let the AI
                    # take its first attempt.
                    # =============================================

                    print(
                        "\n🔄 Docker failure stored."
                    )

                    print(
                        "AI will analyze the Docker failure "
                        "on the next attempt."
                    )

                    continue


    # ========================================================
    # READ SOURCE FILES
    # ========================================================

    # ========================================================
    # READ SOURCE FILES
    # ========================================================

    source_files = project_info.get(
        "source_files",
        []
    )


    source_code = ""


    for source_file in source_files:

        file_path = os.path.join(
            project_path,
            source_file
        )


        source_code += f"""

===== FILE: {source_file} =====

{read_file(file_path)}
"""


    # ========================================================
    # FAILED FIX INFORMATION
    # ========================================================

    failed_fix_info = ""


    if failed_fixes:

        failed_fix_info = """

PREVIOUS FAILED FIXES:

"""


        for failed in failed_fixes[-3:]:

            failed_fix_info += f"""

FILE:
{failed["file"]}

OLD:
{failed["old"]}

NEW:
{failed["new"]}

ERROR:
{failed["error"]}

----------------------------------------
"""
     # ========================================================
    # DEBUG: SHOW WHAT'S ACTUALLY BEING SENT TO THE A


    # ========================================================
    # CREATE PROMPT
    # ========================================================

    if debug_type in ("docker_build", "docker_runtime"):

        print("\n===== DOCKER DEBUGGING MODE =====")

        dockerfile_path = os.path.join(
            project_path,
            "Dockerfile"
        )

        if os.path.exists(dockerfile_path):
            dockerfile_content = read_file(
                dockerfile_path
            )
        else:
            dockerfile_content = "Dockerfile does not exist."


        dockerignore_path = os.path.join(
            project_path,
            ".dockerignore"
        )

        if os.path.exists(dockerignore_path):
            dockerignore_content = read_file(dockerignore_path)
        else:
            dockerignore_content = "No .dockerignore file exists."

        # =====================================================
        # GATE SOURCE CODE FOR BUILD FAILURES
        # =====================================================
        # A docker BUILD failure happens before the container ever
        # runs, so application source code cannot be the cause
        # UNLESS the build error text itself names a source file
        # (e.g. a bad COPY path, missing file, etc).


        if debug_type == "docker_build":
            source_files_list = project_info.get("source_files", [])

            mentions_source_file = any(
                os.path.basename(f) in error
                for f in source_files_list
            )

            if mentions_source_file:
                docker_source_code = source_code
            else:
                docker_source_code = (
                    "(omitted — this is a Docker BUILD failure and the "
                    "build error does not reference any application "
                    "source file. The problem is almost certainly in "
                    "the Dockerfile itself, not the application code.)"
                )
        else:
            # docker_runtime failures can legitimately involve app code
            docker_source_code = source_code

        print("\n===== DEBUG: SOURCE CODE SENT TO DOCKER PROMPT =====")
        print(docker_source_code)

        prompt = docker_failure_prompt(
            project_path,
            app_file,
            error,
            docker_source_code,
            dockerfile_content,
            dockerignore_content,
            project_info,
            failed_fix_info=failed_fix_info
        )+ extra_instructions


    elif test_info:

        prompt = test_failure_prompt(
            project_path,
            app_file,
            error,
            source_code,
            test_info,
            project_info.get(
                "source_files",
                []
            ),
            failed_fix_info=failed_fix_info
        )

    else:

        prompt = application_error_prompt(
            project_path,
            app_file,
            error,
            source_code,
            project_info.get(
                "source_files",
                []
            ),
            failed_fix_info=failed_fix_info
        )


    # ========================================================
    # SKIP AI FOR EXTERNAL INFRASTRUCTURE FAILURES
    # ========================================================

     
    if debug_type == "docker_infrastructure":

        print("\n⚠️ SKIPPING AI — EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
        print(
            "This appears to be a registry/network issue, not a "
            "problem with the project. Retrying the same Dockerfile "
            "unchanged, since these failures are often transient."
        )

        if attempt == MAX_ATTEMPTS:
            print("\n❌ Maximum attempts reached. Giving up.")
            break

        error = ""
        continue


    # ========================================================
    # ASK LLM FOR FIX
    # ========================================================

    print("\n===== ASKING AI FOR FIX =====")


    try:

        response = ollama.chat(

            model="qwen2.5-coder:3b",

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


    except Exception as e:

        print("\n❌ ERROR COMMUNICATING WITH AI")

        print(e)

        break


    # ========================================================
    # READ AI RESPONSE
    # ========================================================

    print("\n===== RAW AI RESPONSE =====")

    print(response.message.content)


    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        fix = json.loads(
            response.message.content
        )


    except json.JSONDecodeError as e:

        print("\n❌ AI returned invalid JSON")

        print(e)


        if attempt == MAX_ATTEMPTS:

            print(
                "\n❌ Maximum attempts reached."
            )

            break


        continue


    # ========================================================
    # CHECK REQUIRED FIELDS
    # ========================================================

    required_fields = [

        "file",

        "old",

        "new",

        "reason"

    ]


    missing = [

        field

        for field in required_fields

        if field not in fix

    ]


    if missing:

        print(
            "\n❌ AI response missing fields:"
        )

        print(missing)

        continue




    # ========================================================
    # HANDLE EXTERNAL DOCKER FAILURE
    # ========================================================
    if (
        debug_type in ("docker_build", "docker_runtime")
        and not fix["file"]
    ):

        print(
            "\n⚠️ DOCKER FAILURE IS EXTERNAL"
        )

        print(
            "\nREASON:"
        )

        print(
            fix["reason"]
        )

        print(
            "\nNo project file will be modified."
        )

        break


    # ========================================================
    # REJECT REPEATED FIX
    # ========================================================

    if is_repeated_fix(fix, failed_fixes):

        print("\n❌ AI repeated a fix that already failed.")
        print("FILE:", fix["file"])
        print("OLD:", fix["old"])

        repeat_count = len([
            f for f in failed_fixes
            if f["old"] == fix["old"]
        ])

        failed_fixes.append({
            "file": fix["file"],
            "old": fix["old"],
            "new": fix["new"],
            "error": (
                f"REPEATED {repeat_count} TIME(S) — DO NOT PROPOSE "
                f"THIS SAME OLD/NEW PAIR AGAIN. Look closely at the "
                f"actual error and propose a structurally different fix."
            )
        })

        if attempt == MAX_ATTEMPTS:
            print("\n❌ Maximum attempts reached.")
            break

        print("\n🔄 Skipping validation. Asking AI for a different fix...")
        continue


    # ========================================================
    # NORMALIZE FILE PATH
    # ========================================================

    source_files = project_info.get(
    "source_files",
    []
)

    allowed_files = list(source_files)

    if os.path.exists(
        os.path.join(project_path, "Dockerfile")
    ):
        allowed_files.append("Dockerfile")

    if os.path.exists(
        os.path.join(project_path, ".dockerignore")
    ):
        allowed_files.append(".dockerignore")

    project_root = os.path.abspath(project_path)

    raw_selected_file = fix["file"]

    # --------------------------------------------------------
    # Normalize slashes and strip any leading "./"
    # --------------------------------------------------------

    normalized = raw_selected_file.replace("\\", "/").strip()

    if normalized.startswith("./"):
        normalized = normalized[2:]

    # --------------------------------------------------------
    # If it's absolute, make it relative to the project root
    # --------------------------------------------------------

    if os.path.isabs(normalized):
        normalized = os.path.relpath(normalized, project_root)
        normalized = normalized.replace("\\", "/")

    # --------------------------------------------------------
    # Match against known source files by exact match OR suffix.
    # This handles any junk prefix the model adds (project folder
    # name, nested path, "src/", etc.) regardless of project layout.
    # --------------------------------------------------------

    selected_file = None

    for candidate in allowed_files:

        candidate_normalized = candidate.replace("\\", "/")

        if normalized == candidate_normalized:
            selected_file = candidate
            break

        if normalized.endswith("/" + candidate_normalized):
            selected_file = candidate
            break

    # --------------------------------------------------------
    # CHECK ALLOWED SOURCE FILE
    # --------------------------------------------------------

    if selected_file is None:

        print(
            "\n❌ AI proposed an invalid source file."
        )

        print(
            "Allowed source files:"
        )

        print(allowed_files)

        print(
            "Received:"
        )

        print(fix["file"])

        continue

    fix["file"] = selected_file


    # ========================================================
    # HARD GATE: DOCKER BUILD FAILURES CANNOT BE FIXED
    # BY MODIFYING APPLICATION SOURCE
    # ========================================================

    if (
        debug_type == "docker_build"
        and fix["file"] not in ("Dockerfile", "")
    ):

        print(
            "\n⚠️ REJECTED: AI proposed modifying "
            f"'{fix['file']}' for a Docker BUILD failure."
        )

        print(
            "Build failures happen before the container runs, so "
            "application source code cannot be responsible. "
            "Re-prompting with a stricter instruction."
        )

        extra_instructions = (
            "\n\nIMPORTANT CORRECTION: Your previous answer proposed "
            f"modifying '{fix['file']}', but this is a Docker BUILD "
            "failure — the container never ran, so application source "
            "code cannot be the cause. You must either propose a change "
            "to the Dockerfile, or return file=\"\" if this is an "
            "external infrastructure issue."
        )

        if attempt == MAX_ATTEMPTS:
            print("\n❌ Maximum attempts reached.")
            break

        continue

    extra_instructions = ""



    # ========================================================
    # READ SELECTED FILE
    # ========================================================

    selected_file_path = os.path.join(

        project_path,

        fix["file"]

    )


    code = read_file(
        selected_file_path
    )


    # ========================================================
    # SHOW PROPOSED FIX
    # ========================================================

    print("\n===== PROPOSED FIX =====")


    print("\nFILE:")

    print(fix["file"])


    print("\nOLD:")

    print(fix["old"])


    print("\nNEW:")

    print(fix["new"])


    print("\nREASON:")

    print(fix["reason"])


   # ========================================================
    # VALIDATE FIX
    # ========================================================

    print("\n===== VALIDATING FIX =====")


    if fix["file"] == "Dockerfile":

        validation = validate_dockerfile_fix(
            code,
            fix["old"],
            fix["new"]
        )

    elif fix["file"] == ".dockerignore":

        validation = validate_dockerignore_fix(
            code,
            fix["old"],
            fix["new"]
        )

    else:

        validation = validate_python_fix(
            code,
            fix["old"],
            fix["new"]
        )


    if not validation["valid"]:
        print("\n❌ FIX REJECTED")
        print("REASON:")
        print(validation["reason"])

        print("\n===== IMPORTANT: CURRENT SOURCE CODE =====")
        print(code)

        print("\nThe next AI response MUST choose 'old' from the source above.")

        # Record this so the AI sees it on the next prompt
        # instead of repeating the same mistake blind.
        failed_fixes.append({
            "file": fix.get("file", ""),
            "old": fix.get("old", ""),
            "new": fix.get("new", ""),
            "error": (
                "VALIDATION REJECTED THIS AI RESPONSE. "
                "The proposed OLD value does not exist in the CURRENT SOURCE CODE. "
                "On the next attempt, inspect CURRENT SOURCE CODE again and copy "
                "the OLD value character-for-character from it. "
                f"Validator reason: {validation['reason']}"
            )
        })

        if attempt == MAX_ATTEMPTS:
            print(
                "\n❌ Maximum attempts reached."
            )
            break

        print(
            "\n🔄 Invalid fix. Asking AI for another fix..."
        )
        continue


    print("\n✅ FIX VALIDATION PASSED")

    print(validation["reason"])


    # ========================================================
    # HUMAN APPROVAL
    # ========================================================

    choice = input(
        "\nApply this fix? [y/n]: "
    )


    if choice.lower() != "y":

        print(
            "\n❌ Fix rejected by human."
        )

        break


    # ========================================================
    # CREATE GIT CHECKPOINT
    # ========================================================

    print(
        "\n===== CREATING GIT CHECKPOINT ====="
    )


    checkpoint = git_checkpoint(project_path)

    if not checkpoint["success"]:
        print("❌ Could not create Git checkpoint.")
        break

    checkpoint_commit = checkpoint["checkpoint"]

    print(
        "✅ Git checkpoint created."
    )


    # ========================================================
    # MODIFY FILE
    # ========================================================

    result = modify_file(

        selected_file_path,

        validation["resolved_old"],

        fix["new"]

    )




    print("\n" + result)


    if result != "CHANGE APPLIED successfully.":

        print(
            "\n❌ Fix could not be applied."
        )

        break


    # ========================================================
    # VERIFY APPLICATION
    # ========================================================

    print(
        "\n===== VERIFYING FIX ====="
    )


    verify = run_project(
        project_info
    )


    # ========================================================
    # APPLICATION STILL FAILS
    # ========================================================

    if verify["returncode"] != 0:

        print(
            "\n❌ APPLICATION STILL FAILS"
        )


        print("\nNEW ERROR:")

        print(
            verify["stderr"]
        )


        # ----------------------------------------------------
        # CHECK IF THIS FIX MADE PROGRESS
        # (new error is DIFFERENT from the error that existed
        # before this fix was applied)
        # ----------------------------------------------------

        made_progress = (verify["stderr"] != last_error)


        if made_progress:

            # ------------------------------------------------
            # KEEP THE FIX — it changed the error, that's
            # forward progress even though it's not fully fixed.
            # ------------------------------------------------

            print(
                "\n✅ Progress made — new error is different. "
                "Keeping this fix."
            )

            error = verify["stderr"]

            last_error = verify["stderr"]

            test_info = ""

            attempt = 0

            continue


        # ----------------------------------------------------
        # NO PROGRESS — roll back
        # ----------------------------------------------------

        # Only NOW is this a genuine failed fix — log it so the
        # AI knows not to propose it again. Fixes that were kept
        # (made_progress == True, above) must NOT be logged here,
        # or PREVIOUS FAILED FIXES ends up full of stale old/new
        # pairs referencing code that no longer exists in the
        # file, which the model can hallucinate-blend together.
        failed_fixes.append({
            "file": fix["file"],
            "old": fix["old"],
            "new": fix["new"],
            "error": verify["stderr"]
        })

        print(
            "\n===== ROLLING BACK FAILED FIX (no progress) ====="
        )

        rollback = git_rollback(
            project_path,
            checkpoint_commit
        )

        if not rollback["success"]:

            print(
                "\n❌ Git rollback failed."
            )

            print(
                rollback["stderr"]
            )

            break

        print(
            "✅ Failed fix rolled back."
        )

        error = verify["stderr"]

        last_error = verify["stderr"]

        test_info = ""

        continue


    # ========================================================
    # APPLICATION SUCCESS
    # ========================================================

    print(
        "\n✅ APPLICATION RUNS"
    )


    print(
        "\nAPPLICATION OUTPUT:"
    )


    print(
        verify["stdout"]
    )


    # ========================================================
    # RUN TESTS AFTER FIX
    # ========================================================

    if project_info.get("test_framework"):

        print(
            "\n===== RUNNING TESTS ====="
        )


        test_result = run_tests(
            project_path
        )


        print(
            "\n===== TEST OUTPUT ====="
        )


        print(
            test_result["stdout"]
        )


        if test_result["stderr"]:

            print(
                "\n===== TEST ERROR ====="
            )

            print(
                test_result["stderr"]
            )


        print(
            "\n===== TEST RETURN CODE ====="
        )


        print(
            test_result["returncode"]
        )


        # ====================================================
        # TESTS PASS
        # ====================================================

        if test_result["returncode"] == 0:

            print(
                "\n✅ ALL TESTS PASSED"
            )


            # =================================================
            # DOCKER VALIDATION
            # =================================================

            print(
                "\n===== RUNNING DOCKER VALIDATION ====="
            )


            docker_result = build_and_run_docker(
                project_path,
                entry_point=project_info["entry_point"],
                project_info=project_info
            )


            print(
                "\n===== DOCKER BUILD STDOUT ====="
            )


            print(
                docker_result["build_stdout"]
            )


            print(
                "\n===== DOCKER BUILD STDERR ====="
            )


            print(
                docker_result["build_stderr"]
            )


            print(
                "\n===== DOCKER BUILD RETURN CODE ====="
            )


            print(
                docker_result["build_returncode"]
            )


            print(
                "\n===== DOCKER CONTAINER STDOUT ====="
            )


            print(
                docker_result["run_stdout"]
            )


            print(
                "\n===== DOCKER CONTAINER STDERR ====="
            )


            print(
                docker_result["run_stderr"]
            )


            print(
                "\n===== DOCKER CONTAINER RETURN CODE ====="
            )


            print(
                docker_result["run_returncode"]
            )


            # =================================================
            # DOCKER PASSED
            # =================================================

            if (
                docker_result["build_returncode"] == 0
                and docker_result["run_returncode"] == 0
            ):

                print(
                    "\n✅ DOCKER VALIDATION PASSED"
                )


                # =============================================
                # COMMIT
                # =============================================

                print(
                    "\n===== COMMITTING SUCCESSFUL FIX ====="
                )

                commit_result = git_commit_success(
                    project_path
                )

                if not commit_result["success"]:

                    print(
                        "\n❌ Could not commit successful fix."
                    )

                    print(
                        commit_result["stderr"]
                    )

                    break

                print(
                    "✅ Successful fix committed."
                )

                print(
                    "\n🎉 FIX SUCCESSFUL"
                )

                break


            # =================================================
            # DOCKER FAILED
            # =================================================

            else:

                print(
                    "\n❌ DOCKER VALIDATION FAILED"
                )

                if docker_result["build_returncode"] != 0:
                    debug_type = "docker_build"
                else:
                    debug_type = "docker_runtime"

                stored_debug_type = debug_type

                print(f"\n===== DEBUG: CLASSIFIED FAILURE AS: {debug_type} =====")


                if is_docker_infrastructure_error(docker_result):
                            print("\n⚠️ DETECTED EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
                            print("This looks like a registry/network issue, not a project problem.")
                            debug_type = "docker_infrastructure"
                            stored_debug_type = debug_type



                error = (

                    "The application and local tests passed, "

                    "but the application failed inside Docker.\n\n"

                    "DOCKER BUILD STDOUT:\n"

                    + docker_result["build_stdout"]

                    + "\n\nDOCKER BUILD STDERR:\n"

                    + docker_result["build_stderr"]

                    + "\n\nDOCKER CONTAINER STDOUT:\n"

                    + docker_result["run_stdout"]

                    + "\n\nDOCKER CONTAINER STDERR:\n"

                    + docker_result["run_stderr"]

                )


                test_info = build_test_info(
                    project_path,
                    project_info,
                    test_result
                )


                failed_fixes.append({

                    "file": fix["file"],

                    "old": fix["old"],

                    "new": fix["new"],

                    "error": error

                })


                # =============================================
                # ROLLBACK
                # =============================================

                print(
                    "\n===== ROLLING BACK DOCKER FAILED FIX ====="
                )


                rollback = git_rollback(
                    project_path,
                    checkpoint_commit
                )


                if not rollback["success"]:

                    print(
                        "\n❌ Git rollback failed."
                    )

                    print(
                        rollback["stderr"]
                    )

                    break


                print(
                    "✅ Docker failed fix rolled back."
                )


                if attempt == MAX_ATTEMPTS:

                    print(
                        "\n❌ Maximum attempts reached."
                    )

                    break


                print(
                    "\n🔄 Docker failure stored."
                )

                print(
                    "AI will analyze the Docker failure "
                    "on the next attempt."
                )


                continue


        # ====================================================
        # TESTS FAILED AFTER FIX
        # ====================================================

        else:

            print(
                "\n❌ TESTS FAILED"
            )


            current_failed_count = count_failed_tests(
                test_result["stdout"]
            )


            made_progress = current_failed_count < last_failed_count


            if made_progress:

                # ----------------------------------------------
                # KEEP THE FIX — fewer tests are failing now.
                # ----------------------------------------------

                print(
                    f"\n✅ Progress made — failed test count "
                    f"dropped from {last_failed_count} to "
                    f"{current_failed_count}. Keeping this fix."
                )

                last_failed_count = current_failed_count

                attempt = 0

            else:

                # ----------------------------------------------
                # ROLLBACK — no improvement, or it got worse.
                #
                # Only NOW is this a genuine failed fix — log it
                # so the AI knows not to propose it again. Fixes
                # that were kept (made_progress == True, above)
                # must NOT be logged here, or PREVIOUS FAILED
                # FIXES ends up full of stale old/new pairs
                # referencing code that no longer exists in the
                # file, which the model can hallucinate-blend
                # together into fabricated "old" text.
                # ----------------------------------------------

                failed_fixes.append({

                    "file": fix["file"],

                    "old": fix["old"],

                    "new": fix["new"],

                    "error": (
                        test_result["stdout"]
                        + "\n"
                        + test_result["stderr"]
                    )

                })

                print(
                    "\n===== ROLLING BACK FAILED FIX "
                    "(no test progress) ====="
                )

                rollback = git_rollback(
                    project_path,
                    checkpoint_commit
                )

                if not rollback["success"]:

                    print(
                        "\n❌ Git rollback failed."
                    )

                    print(
                        rollback["stderr"]
                    )

                    break

                print(
                    "✅ Failed fix rolled back."
                )


            # ------------------------------------------------
            # STORE TEST ERROR
            # ------------------------------------------------

            error = (

                "The application runs successfully, "

                "but the automated tests are failing.\n\n"

                "TEST OUTPUT:\n"

                + test_result["stdout"]

                + "\n\nTEST ERROR:\n"

                + test_result["stderr"]

            )


            test_info = build_test_info(
                project_path,
                project_info,
                test_result
            )


            print(
                "🔄 Test failure stored."
            )

            print(
                "AI will analyze the test failure again."
            )


            if attempt == MAX_ATTEMPTS:

                print(
                    "\n❌ Maximum attempts reached."
                )

                break


            continue


    # ========================================================
    # NO TEST FRAMEWORK AFTER FIX
    # ========================================================

    else:

        print(
            "\n⚠️ No test framework detected."
        )


        # ====================================================
        # DOCKER VALIDATION
        # ====================================================

        print(
            "\n===== RUNNING DOCKER VALIDATION ====="
        )


        docker_result = build_and_run_docker(
            project_path,
            entry_point=project_info["entry_point"],
            project_info=project_info
        )


        print(
            "\n===== DOCKER BUILD STDOUT ====="
        )


        print(
            docker_result["build_stdout"]
        )


        print(
            "\n===== DOCKER BUILD STDERR ====="
        )


        print(
            docker_result["build_stderr"]
        )


        print(
            "\n===== DOCKER BUILD RETURN CODE ====="
        )


        print(
            docker_result["build_returncode"]
        )


        print(
            "\n===== DOCKER CONTAINER STDOUT ====="
        )


        print(
            docker_result["run_stdout"]
        )


        print(
            "\n===== DOCKER CONTAINER STDERR ====="
        )


        print(
            docker_result["run_stderr"]
        )


        print(
            "\n===== DOCKER CONTAINER RETURN CODE ====="
        )


        print(
            docker_result["run_returncode"]
        )


        # ====================================================
        # DOCKER PASSED
        # ====================================================

        if (
            docker_result["build_returncode"] == 0
            and docker_result["run_returncode"] == 0
        ):

            print(
                "\n✅ DOCKER VALIDATION PASSED"
            )


            print(
                "\n===== COMMITTING SUCCESSFUL FIX ====="
            )


            commit_result = git_commit_success(
                project_path
            )


            if not commit_result["success"]:

                print(
                    "\n❌ Could not commit successful fix."
                )

                print(
                    commit_result["stderr"]
                )

                break


            print(
                "✅ Successful fix committed."
            )


            print(
                "\n🎉 FIX SUCCESSFUL"
            )


            break


        # ====================================================
        # DOCKER FAILED
        # ====================================================

        else:

            print(
                "\n❌ DOCKER VALIDATION FAILED"
            )

            if docker_result["build_returncode"] != 0:
                debug_type = "docker_build"
            else:
                debug_type = "docker_runtime"
            stored_debug_type = debug_type

            print(f"\n===== DEBUG: CLASSIFIED FAILURE AS: {debug_type} =====")


            if is_docker_infrastructure_error(docker_result):
                            print("\n⚠️ DETECTED EXTERNAL DOCKER INFRASTRUCTURE FAILURE")
                            print("This looks like a registry/network issue, not a project problem.")
                            debug_type = "docker_infrastructure"
                            stored_debug_type = debug_type


            error = (

                "The application runs successfully locally, "

                "but failed inside Docker.\n\n"

                "DOCKER BUILD STDOUT:\n"

                + docker_result["build_stdout"]

                + "\n\nDOCKER BUILD STDERR:\n"

                + docker_result["build_stderr"]

                + "\n\nDOCKER CONTAINER STDOUT:\n"

                + docker_result["run_stdout"]

                + "\n\nDOCKER CONTAINER STDERR:\n"

                + docker_result["run_stderr"]

            )


            failed_fixes.append({

                "file": fix["file"],

                "old": fix["old"],

                "new": fix["new"],

                "error": error

            })


            print(
                "\n===== ROLLING BACK DOCKER FAILED FIX ====="
            )


            rollback = git_rollback(
                project_path,
                checkpoint_commit
            )


            if not rollback["success"]:

                print(
                    "\n❌ Git rollback failed."
                )

                print(
                    rollback["stderr"]
                )

                break


            print(
                "✅ Docker failed fix rolled back."
            )


            if attempt == MAX_ATTEMPTS:

                print(
                    "\n❌ Maximum attempts reached."
                )

                break


            continue


    print("\n========================================")
    print("        DEVOPS AGENT FINISHED")
    print("========================================")
