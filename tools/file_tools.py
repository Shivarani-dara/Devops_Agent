import re


_QUOTE_MAP = {
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2017": "'", "\u2015": "'",
}


def normalize_quotes(text):
    for bad, good in _QUOTE_MAP.items():
        text = text.replace(bad, good)
    return text


def fuzzy_locate(content, old_text):
    """
    Find the real substring in content that the AI was trying to
    reference, tolerating:

    - whitespace differences (added, removed, or reformatted --
      e.g. "a/0" vs "a / 0" vs "a  /  0" all match each other)
    - smart quotes
    - single vs double quotes

    Returns the ACTUAL text from content, or None.
    """

    content_norm = normalize_quotes(content)
    old_norm = normalize_quotes(old_text).strip("\n")

    # Tokenize into identifiers/numbers (\w+) vs individual
    # punctuation/operator characters (\S). Whitespace is dropped
    # entirely by findall since it matches neither pattern.
    #
    # Joining the tokens back together with \s* (zero-or-more)
    # between EVERY pair means whitespace becomes fully optional
    # at every position -- not just where the AI's text happened
    # to include a space. This is what lets "a/0" match "a / 0"
    # regardless of which one the AI wrote and which one is in
    # the real file.
    tokens = re.findall(r"\w+|\S", old_norm)

    if not tokens:
        return None

    pattern = r"\s*".join(re.escape(tok) for tok in tokens)

    # Temporarily replace quote characters with a placeholder.
    # This prevents the replacement from modifying its own regex.
    QUOTE_PLACEHOLDER = "__QUOTE_PLACEHOLDER__"

    pattern = pattern.replace(
        "'",
        QUOTE_PLACEHOLDER
    )

    pattern = pattern.replace(
        '"',
        QUOTE_PLACEHOLDER
    )

    # Allow either single or double quote
    pattern = pattern.replace(
        QUOTE_PLACEHOLDER,
        r"""['"]"""
    )

    match = re.search(
        pattern,
        content_norm,
        re.MULTILINE
    )

    if not match:
        return None

    start, end = match.span()

    # Return the ORIGINAL source text,
    # not the normalized version.
    return content[start:end]

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
            real_old = fuzzy_locate(content, old_text)
            if real_old is None:
                return "ERROR: The old code was not found in the file."
            old_text = real_old

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