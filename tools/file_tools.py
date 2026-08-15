def read_file(filename):
    try:
        with open(filename, "r") as file:
            return file.read()

    except Exception as e:
        return f"ERROR reading file: {e}"


def modify_file(filename, old_text, new_text):
    try:
        with open(filename, "r") as file:
            content = file.read()

        if old_text not in content:
            return "ERROR: The old code was not found in the file."

        if old_text.strip() == new_text.strip():
            return "ERROR: OLD and NEW code are identical."

        print("\n=== PROPOSED CHANGE ===")
        print(f"File: {filename}")

        print("\n--- OLD ---")
        print(old_text)

        print("\n--- NEW ---")
        print(new_text)

        content = content.replace(old_text, new_text, 1)

        with open(filename, "w") as file:
            file.write(content)

        return "CHANGE APPLIED successfully."

    except Exception as e:
        return f"ERROR modifying file: {e}"