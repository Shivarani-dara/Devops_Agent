import ast
import re

from tools.file_tools import fuzzy_locate


def validate_python_fix(content, old_text, new_text):
    """
    Validate a proposed Python code change
    without modifying the actual file.
    """

    # CHECK 1: Reject empty OLD text
    # An empty string is trivially "found" at position 0 of ANY
    # file, so an empty "old" would silently PREPEND new code
    # instead of replacing anything — duplicating functions.
    if not old_text or not old_text.strip():
        return {
            "valid": False,
            "reason": (
                "OLD code cannot be empty. You must specify the "
                "exact existing code to replace."
            )
        }

    # CHECK 2: OLD code must exist in the file
    # Tries an exact match first; if that fails, tries fuzzy_locate
    # (tolerates curly-quote corruption, straight-quote style
    # differences, and minor whitespace drift).
    if old_text not in content:
        real_old = fuzzy_locate(content, old_text)
        if real_old is None:
            return {
                "valid": False,
                "reason": "OLD code was not found in the source file."
            }
        old_text = real_old

    # CHECK 3: OLD code must be UNIQUE in the file
    # If the same line appears more than once (e.g. identical
    # "return a - b" in two different functions), content.replace()
    # would silently edit the FIRST occurrence — which may not be
    # the one the model meant, corrupting the wrong function.
    occurrence_count = content.count(old_text)
    if occurrence_count > 1:
        return {
            "valid": False,
            "reason": (
                f"OLD code is ambiguous — it appears {occurrence_count} "
                f"times in the file. You MUST include the full function "
                f"signature (the 'def <name>(...):' line) directly above "
                f"the code, so it becomes unique. For example, instead "
                f"of just:\n\n{old_text}\n\nwrite it as:\n\n"
                f"def <the_actual_function_name>(...):\n    {old_text}"
            )
        }

    # CHECK 4: OLD and NEW must actually differ
    if old_text.strip() == new_text.strip():
        return {
            "valid": False,
            "reason": "OLD and NEW code are identical."
        }

    # CHECK 5: Reject single-line "if ... else ..."
    # "if x: y else: z" on ONE line is never valid Python.
    if re.search(r'\bif\b.*:.*\belse\b.*:', new_text):
        return {
            "valid": False,
            "reason": (
                "NEW code contains an 'if ... else ...' on a single "
                "line, which is not valid Python. Rewrite as a proper "
                "multi-line if/else block."
            )
        }

    # CHECK 6: If OLD was a return statement, NEW must be too
    # Dropping "return" turns a real fix into a silent no-op that
    # makes the function return None — compile() alone can't catch
    # this since it's still grammatically valid.
    old_stripped = old_text.strip()
    new_stripped = new_text.strip()
    if old_stripped.startswith("return") and not new_stripped.startswith("return"):
        return {
            "valid": False,
            "reason": (
                "The OLD code was a return statement, but NEW code "
                "is not. This would silently make the function "
                "return None. Add 'return' back."
            )
        }

    # Build the proposed file content in memory (not written yet)
    modified_content = content.replace(old_text, new_text, 1)

    # CHECK 7: Full syntax + semantic validity
    # Uses compile(), not ast.parse() — compile() catches things
    # like "return outside function" that ast.parse() misses.
    try:
        compile(modified_content, "<string>", "exec")
    except SyntaxError as e:
        return {
            "valid": False,
            "reason": f"Proposed code contains a syntax error: {e}"
        }

    return {
        "valid": True,
        "reason": "Proposed Python code is syntactically valid.",
        "content": modified_content,
        "resolved_old": old_text
    }



def validate_dockerfile_fix(content, old_text, new_text):
    """
    Validate a proposed Dockerfile change
    without modifying the actual file.
    """

    # CHECK 1: OLD cannot be empty
    if not old_text or not old_text.strip():
        return {
            "valid": False,
            "reason": "OLD Dockerfile code cannot be empty."
        }

    # CHECK 2: OLD must exist
    if old_text not in content:
        return {
            "valid": False,
            "reason": (
                "OLD Dockerfile code was not found "
                "in the current Dockerfile."
            )
        }

    # CHECK 3: OLD must be unique
    occurrence_count = content.count(old_text)

    if occurrence_count > 1:
        return {
            "valid": False,
            "reason": (
                f"OLD Dockerfile code is ambiguous — "
                f"it appears {occurrence_count} times."
            )
        }

    # CHECK 4: OLD and NEW must differ
    if old_text.strip() == new_text.strip():
        return {
            "valid": False,
            "reason": "OLD and NEW Dockerfile code are identical."
        }

    # Build proposed Dockerfile in memory
    modified_content = content.replace(
        old_text,
        new_text,
        1
    )

    # Basic Dockerfile sanity checks
    lines = modified_content.splitlines()

    instructions = {
        "FROM",
        "RUN",
        "CMD",
        "ENTRYPOINT",
        "COPY",
        "ADD",
        "WORKDIR",
        "ENV",
        "EXPOSE",
        "USER",
        "ARG",
        "LABEL",
        "VOLUME",
        "HEALTHCHECK",
        "SHELL",
        "STOPSIGNAL"
    }

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        instruction = stripped.split()[0].upper()

        if instruction not in instructions:
            return {
                "valid": False,
                "reason": (
                    f"Proposed Dockerfile contains an "
                    f"unknown instruction: {instruction}"
                )
            }

    return {
        "valid": True,
        "reason": "Proposed Dockerfile is structurally valid.",
        "content": modified_content,
        "resolved_old": old_text
    }

def validate_dockerignore_fix(content, old_text, new_text):

    if not old_text or not old_text.strip():
        return {
            "valid": False,
            "reason": "OLD value is empty."
        }

    if old_text not in content:
        return {
            "valid": False,
            "reason": "OLD Dockerignore text was not found in the current .dockerignore file."
        }

    occurrence_count = content.count(old_text)

    if occurrence_count > 1:
        return {
            "valid": False,
            "reason": "OLD text appears more than once in .dockerignore; it must be unique."
        }

    if old_text == new_text:
        return {
            "valid": False,
            "reason": "OLD and NEW are identical; no actual change proposed."
        }

    modified_content = content.replace(
        old_text,
        new_text,
        1
    )

    return {
        "valid": True,
        "reason": "Proposed .dockerignore change is structurally valid.",
        "content": modified_content,
        "resolved_old": old_text
    }