import ollama
import json
import sys
import os

from tools.file_tools import read_file, modify_file
from core.validator import validate_python_fix
from project.scanner import scan_project
from project.runner import run_project
from tools.test_tools import run_tests
from prompts.debug_prompts import (
    application_error_prompt,
    test_failure_prompt
)


MAX_ATTEMPTS = 3


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


app_file = os.path.join(project_path, entry_point)



# ============================================================
# ERROR STATE
# ============================================================

error = ""
test_info = ""


# ============================================================
# MAIN AGENT LOOP
# ============================================================

for attempt in range(1, MAX_ATTEMPTS + 1):

    print("\n==============================")
    print(f"       ATTEMPT {attempt}")
    print("==============================")

    # ========================================================
    # RUN PROJECT ONLY WHEN WE DON'T ALREADY HAVE AN ERROR
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
                    print("\n🎉 PROJECT SUCCESSFUL")

                    break

                # ------------------------------------------------
                # TESTS FAIL
                # ------------------------------------------------

                else:

                    print("\n❌ TESTS FAILED")

                    if attempt == MAX_ATTEMPTS:

                        print("\n❌ Maximum attempts reached.")
                        break

                    # Store test failure for AI
                    error = (
                        "The application runs successfully, "
                        "but the automated tests are failing.\n\n"
                        "TEST OUTPUT:\n"
                        + test_result["stdout"]
                        + "\n\nTEST ERROR:\n"
                        + test_result["stderr"]
                    )

                    test_info = f"""
AUTOMATED TEST INFORMATION:

Test framework:
{project_info.get("test_framework")}

Test stdout:
{test_result["stdout"]}

Test stderr:
{test_result["stderr"]}

Test return code:
{test_result["returncode"]}
"""

                    print("\n🔄 Test failure stored.")
                    print("AI will analyze the test failure next.")

                    continue

            # ------------------------------------------------
            # NO TEST FRAMEWORK
            # ------------------------------------------------

            else:

                print("\n⚠️ No test framework detected.")
                print("\n🎉 APPLICATION SUCCESSFUL")

                break

    # ========================================================
    # READ CURRENT SOURCE CODE
    # ========================================================

    code = read_file(app_file)

    # ========================================================
# CREATE PROMPT
# ========================================================

    if test_info:
        prompt = test_failure_prompt(
                project_path,
                app_file,
                error,
                code,
                test_info
            )
    else:
         prompt = application_error_prompt(
                project_path,
                app_file,
                error,
                code
            )
    # ========================================================
    # ASK LLM FOR FIX
    # ========================================================

    print("\n===== ASKING AI FOR FIX =====")

    try:
        response = ollama.chat(
             model="llama3.2:latest",

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

        fix = json.loads(response.message.content)

    except json.JSONDecodeError as e:

        print("\n❌ AI returned invalid JSON")
        print(e)

        if attempt == MAX_ATTEMPTS:
            print("\n❌ Maximum attempts reached.")

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
        field for field in required_fields
        if field not in fix
    ]

    if missing:

        print("\n❌ AI response missing fields:")
        print(missing)

        continue


    # ========================================================
    # CHECK FILE PATH
    # ========================================================

    if fix["file"] != app_file:

        print("\n❌ AI proposed wrong file.")

        print("Expected:")
        print(app_file)

        print("Received:")
        print(fix["file"])

        continue


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

    validation = validate_python_fix(
        code,
        fix["old"],
        fix["new"]
    )


    if not validation["valid"]:

        print("\n❌ FIX REJECTED")

        print("REASON:")
        print(validation["reason"])

        if attempt == MAX_ATTEMPTS:

            print("\n❌ Maximum attempts reached.")
            break

        print("\n🔄 Invalid fix. Asking AI for another fix...")

        continue


    print("\n✅ FIX VALIDATION PASSED")
    print(validation["reason"])


    # ========================================================
    # HUMAN APPROVAL
    # ========================================================

    choice = input("\nApply this fix? [y/n]: ")

    if choice.lower() != "y":

        print("\n❌ Fix rejected by human.")

        break


    # ========================================================
    # MODIFY FILE
    # ========================================================

    result = modify_file(
        fix["file"],
        fix["old"],
        fix["new"]
    )

    print("\n" + result)


    if result != "CHANGE APPLIED successfully.":

        print("\n❌ Fix could not be applied.")

        break


    # ========================================================
    # VERIFY APPLICATION
    # ========================================================

    print("\n===== VERIFYING FIX =====")

    verify = run_project(project_info)


    # ========================================================
    # APPLICATION STILL FAILS
    # ========================================================

    if verify["returncode"] != 0:


         print("\n❌ APPLICATION STILL FAILS")

         print("\nNEW ERROR:")
         print(verify["stderr"])

         if attempt == MAX_ATTEMPTS:
             

             print("\n❌ Maximum attempts reached.")
             break

    # Store the new application error
         error = verify["stderr"]

    # This is no longer a test failure
         test_info = ""

         print("\n🔄 Application error stored.")
         print("AI will analyze it on the next attempt.")

         continue


    # ========================================================
    # APPLICATION SUCCESS
    # ========================================================

    print("\n✅ APPLICATION RUNS")

    print("\nAPPLICATION OUTPUT:")
    print(verify["stdout"])


    # ========================================================
    # RUN TESTS AFTER FIX
    # ========================================================

    if project_info.get("test_framework"):

        print("\n===== RUNNING TESTS =====")

        test_result = run_tests(project_path)

        print("\n===== TEST OUTPUT =====")
        print(test_result["stdout"])

        if test_result["stderr"]:

            print("\n===== TEST ERROR =====")
            print(test_result["stderr"])


        # ----------------------------------------------------
        # TESTS PASS
        # ----------------------------------------------------

        if test_result["returncode"] == 0:

            print("\n✅ ALL TESTS PASSED")
            print("\n🎉 FIX SUCCESSFUL")

            break


        # ----------------------------------------------------
        # TESTS FAIL
        # ----------------------------------------------------

        else:

           print("\n❌ TESTS FAILED")

           if attempt == MAX_ATTEMPTS:

               print("\n❌ Maximum attempts reached.")
               break
           
           

           error = (
              "The application runs successfully, "
               "but the automated tests are failing.\n\n"
                "TEST OUTPUT:\n"
                +test_result["stdout"]
                +"\n\nTEST ERROR:\n"
                + test_result["stderr"]
           )

           test_info = f"""
AUTOMATED TEST INFORMATION:

Test framework:
{project_info.get("test_framework")}

Test stdout:
{test_result["stdout"]}

Test stderr:
{test_result["stderr"]}

Test return code:
{test_result["returncode"]}
"""
    

           print("\n🔄 Test failure stored.")
           print("AI will analyze the test failure on the next attempt.")

           continue

    # ========================================================
    # NO TESTS
    # ========================================================

    else:

        print("\n🎉 FIX SUCCESSFUL")
        break