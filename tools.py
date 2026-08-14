import subprocess

def read_file(filename):
    try:
        with open(filename,"r") as file:
            return file.read()
    except Exception as e:
        return f"Error readingfile:{e}"

def run_command(command):
    try:
        result=subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return f"""
STDOUT:
{result.stdout}

STDERR:
{result.stderr}

RETURN CODE:
{result.returncode}
"""
    except Exception as e:
        return f"error running commands:{e}"


#modify code

def modify_file(filename, old_text, new_text):
    try:
        with open(filename, "r") as f:
            content = f.read()

        # Check whether the AI's old code actually exists
        if old_text not in content:
            return "ERROR: The old code was not found in the file."

        # Don't allow a useless change
        if old_text == new_text:
            return "ERROR: OLD and NEW code are identical."

        print("\n=== PROPOSED CHANGE ===")
        print(f"File: {filename}")

        print("\n--- OLD ---")
        print(old_text)

        print("\n--- NEW ---")
        print(new_text)

        choice = input("\nApply this change? [y/n]: ")

        if choice.lower() != "y":
            return "CHANGE REJECTED by human."

        # Replace the code
        content = content.replace(old_text, new_text, 1)

        with open(filename, "w") as f:
            f.write(content)

        return "CHANGE APPLIED successfully."

    except Exception as e:
        return f"ERROR modifying file: {e}"

if __name__ == "__main__":
    print(read_file("test_project/app.py"))

    result = modify_file(
        "test_project/app.py",
        'x=add_numbers(10,"90")',
        'x=add_numbers(10,90)'
    )

    print(result)

    print("\n===== FILE AFTER CHANGE =====")
    print(read_file("test_project/app.py"))