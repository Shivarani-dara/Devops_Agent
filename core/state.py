from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    # Current debugging information
    error: str = ""
    failure_type: str = "application"

    # Attempt tracking
    attempt: int = 0
    max_attempts: int = 5

    # Previous error
    last_error: str = ""

    # Test information
    test_info: str = ""
    last_failed_count: float = float("inf")

    # Previous fixes that failed
    failed_fixes: list[dict[str, Any]] = field(default_factory=list)

    # Track repeated fixes
    repeated_fix_counts: dict[str, int] = field(default_factory=dict)

    # Additional instructions given to the LLM
    extra_instructions: str = ""

    # Remember the currently stored debugging type
    stored_debug_type: str | None = None