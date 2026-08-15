import ast


def validate_python_fix(content, old_text, new_text):
    """
    Validate a proposed Python code change
    without modifying the actual file.
    """

    # Check OLD code exists
    if old_text not in content:
        return {
            "valid": False,
            "reason": "OLD code was not found in the source file."
        }

    # Check OLD and NEW are different
    if old_text.strip() == new_text.strip():
        return {
            "valid": False,
            "reason": "OLD and NEW code are identical."
        }

    # Create the proposed source code in memory
    modified_content = content.replace(
        old_text,
        new_text,
        1
    )

    # Check Python syntax
    try:
        ast.parse(modified_content)

    except SyntaxError as e:
        return {
            "valid": False,
            "reason": (
                f"Proposed code contains a syntax error: "
                f"{e}"
            )
        }

    return {
        "valid": True,
        "reason": "Proposed Python code is syntactically valid.",
        "content": modified_content
    }