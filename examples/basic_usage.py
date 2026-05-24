"""
Basic usage examples for Agent Governance Framework v2.0.

Run: python examples/basic_usage.py
"""

from src.gate import (pass_gate, register_station, check_track,
                       extract_m, has_panel, set_pattern,
                       get_interception_stats)


def example_1_clean_pass():
    """A properly formatted response with station context passes both checks."""
    print("=" * 60)
    print("Example 1: Clean pass (signal + track dual check)")
    print("=" * 60)

    # Register a station with required output fields
    register_station("describer", "DESCRIBED",
        required_fields=["user_verbatim", "core_intent", "acceptance_criteria"])

    response = (
        "### Task: R1-C1 → M1 | tag:describer | gate:N\n"
        "┌─────────────────┐\n"
        "│  Dispatch Panel  │\n"
        "└─────────────────┘\n"
        "user_verbatim: sort desktop files\n"
        "core_intent: list .md files by size\n"
        "acceptance_criteria: terminal outputs sorted list"
    )
    result = pass_gate(response, station="describer")
    print(f"  ok: {result.ok}")
    print(f"  reason: {result.reason}")
    print()


def example_2_signal_intercept():
    """Missing compliance marker → intercepted, not auto-repaired."""
    print("=" * 60)
    print("Example 2: Missing marker → INTERCEPTED (zero tolerance)")
    print("=" * 60)

    response = "I'll help you with that task."
    result = pass_gate(response)
    print(f"  ok: {result.ok}        # False — intercepted")
    print(f"  reason: {result.reason}  # 'missing-code'")
    print(f"  repaired: {result.repaired}       # Always False in v2.0")
    print()


def example_3_track_violation():
    """Signal passes but track fails → intercepted."""
    print("=" * 60)
    print("Example 3: Track violation (missing required fields)")
    print("=" * 60)

    response = (
        "### Task: R1-C1 → M1 | tag:describer | gate:N\n"
        "┌─────────────────┐\n"
        "│  Dispatch Panel  │\n"
        "└─────────────────┘\n"
        "Some random text without required station fields..."
    )
    result = pass_gate(response, station="describer")
    print(f"  ok: {result.ok}        # False — track failed")
    print(f"  reason: {result.reason[:80]}...")
    print()


def example_4_free_mode():
    """Free mode: signal check only, no track validation."""
    print("=" * 60)
    print("Example 4: Free mode (station=None → signal only)")
    print("=" * 60)

    response = (
        "### Task: R0-C0 → M0 | tag:free | gate:N\n"
        "Any content works here, no station schema applied."
    )
    result = pass_gate(response, station=None)
    print(f"  ok: {result.ok}         # True — signal passes, track skipped")
    print()


def example_5_interception_stats():
    """View interception metrics."""
    print("=" * 60)
    print("Example 5: Interception statistics")
    print("=" * 60)

    stats = get_interception_stats()
    print(f"  Total interceptions: {stats['total']}")
    print(f"  By reason: {stats['by_reason']}")
    if stats['recent']:
        latest = stats['recent'][-1]
        print(f"  Latest: [{latest['station']}] {latest['reason']}")
    print()


if __name__ == "__main__":
    example_1_clean_pass()
    example_2_signal_intercept()
    example_3_track_violation()
    example_4_free_mode()
    example_5_interception_stats()
