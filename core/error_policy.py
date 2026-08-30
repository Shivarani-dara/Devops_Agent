import re


def classify_application_error(error):
    """
    Classify an application failure into a deterministic error type.

    The goal is NOT to solve the error here.
    The goal is to determine what kind of fix the LLM is allowed
    to propose.
    """

    if not error:
        return "unknown"

    error_lower = error.lower()

    # Dependency problems
    if "modulenotfounderror" in error_lower:
        return "dependency"

    if "importerror" in error_lower:
        return "dependency"

    # Python syntax problems
    if "syntaxerror" in error_lower:
        return "syntax"

    if "indentationerror" in error_lower:
        return "indentation"

    # Common runtime errors
    if "nameerror" in error_lower:
        return "name"

    if "typeerror" in error_lower:
        return "type"

    if "indexerror" in error_lower:
        return "index"

    if "keyerror" in error_lower:
        return "key"

    if "attributeerror" in error_lower:
        return "attribute"

    if "zerodivisionerror" in error_lower:
        return "zero_division"

    if "valueerror" in error_lower:
        return "value"

    if "filenotfounderror" in error_lower:
        return "file_not_found"

    if "permissionerror" in error_lower:
        return "permission"

    return "unknown"


def extract_missing_module(error):
    """
    Extract the module name from:

        ModuleNotFoundError: No module named 'flask'

    Returns:
        flask

    or None if no module name can be found.
    """

    if not error:
        return None

    match = re.search(
        r"No module named ['\"]([^'\"]+)['\"]",
        error
    )

    if match:
        return match.group(1)

    return None


def get_allowed_fix_files(error_type, project_info):
    """
    Determine which files the LLM is allowed to modify
    for a particular error type.

    This is a HARD POLICY.
    """

    source_files = project_info.get(
        "source_files",
        []
    )

    requirements_file = project_info.get(
        "requirements_file"
    )

    # --------------------------------------------------
    # DEPENDENCY ERROR
    # --------------------------------------------------

    if error_type == "dependency":

        if requirements_file:
            return [requirements_file]

        return []

    # --------------------------------------------------
    # NORMAL PYTHON APPLICATION ERROR
    # --------------------------------------------------

    if error_type in {
        "syntax",
        "indentation",
        "name",
        "type",
        "index",
        "key",
        "attribute",
        "zero_division",
        "value",
        "file_not_found",
        "permission",
        "unknown"
    }:

        return list(source_files)

    return list(source_files)


def is_allowed_fix_file(
    filename,
    error_type,
    project_info
):
    """
    Check whether the LLM-selected file is allowed
    for this particular error type.
    """

    allowed_files = get_allowed_fix_files(
        error_type,
        project_info
    )

    return filename in allowed_files