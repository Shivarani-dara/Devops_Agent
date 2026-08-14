import ollama
import subprocess
from tools import read_file,modify_file
import json

def run_app():
    result=subprocess.run(
        ["python3","test_project/app.py"],
        capture_output=True,
        text=True
    )
    return result
result=run_app()

if result.returncode!=0:

    error=result.stderr
    code=read_file("test_project/app.py")

    response=ollama.chat(
        model="llama3.2:latest",
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
        "required": ["file", "old", "new", "reason"]
        },
        messages=[
            {
                "role":"user",
                "content":f"""
You are a DevOps debugging agent.

The application app.py failed while running.

Here is the error:

{error}

SOURCE CODE:
{code}

Analyze the error and propose a safe minimal fix.

The exact file path is:
test_project/app.py

IMPORTANT RULES:

1. The "file" field MUST be exactly:
test_project/app.py

2. The "old" field must contain a COMPLETE MEANINGFUL CODE STATEMENT or BLOCK from the source code.

3. NEVER use a single character, variable name, keyword, or tiny fragment as "old".

4. The "old" value must exist EXACTLY in the source code.

5. The "new" value must replace the entire old statement or block.

6. The replacement must actually fix the reported error.

7. Do not modify unrelated code.

8. Do not include markdown.

9. Return ONLY valid JSON.

The JSON must contain:
file
old
new
reason..
"""


            }
        ]
    )
    print("\n=== ERROR =====\n")
    print(error)

    print("\n===== RAW AI RESPONSE =====")
    print(response.message.content)

    
    fix=json.loads(response.message.content)

    fix["file"]="test_project/app.py"
    print("\n===== PROPOSED FIX =====")

    print("FILE:")
    print(fix["file"])

    print("\nOLD:")
    print(fix["old"])

    print("\nNEW:")
    print(fix["new"])

    print("\nREASON:")
    print(fix["reason"])

    choice=input("\n apply this fix [y/n]")

    if choice.lower() == "y":

        result = modify_file(
            fix["file"],
            fix["old"],
            fix["new"]
        )

        print("\n" + result)

        if result == "CHANGE APPLIED successfully.":

            print("\n===== VERIFYING FIX =====")

            verify = run_app()

            if verify.returncode == 0:
                print("\n✅ FIX SUCCESSFUL")
                print("\nAPPLICATION OUTPUT:")
                print(verify.stdout)

            else:
                print("\n❌ FIX FAILED")
                print("\nNEW ERROR:")
                print(verify.stderr)

        else:
            print("\n⚠️ Fix was not applied.")

    else:
        print("\n❌ Fix rejected by human.")