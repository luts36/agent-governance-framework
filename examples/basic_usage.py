"""
Basic usage examples for Agent Governance Framework.

Run: python examples/basic_usage.py
"""

from src.gate import pass_gate, GateResult, extract_m, has_panel, set_pattern


def example_1_clean_pass():
    """A properly formatted response passes cleanly."""
    print("=" * 60)
    print("Example 1: Clean pass (properly formatted)")
    print("=" * 60)
    
    response = (
        "### Task: R1-C1 → M0 | tag:greeting | gate:N\n"
        "Hello! How can I help you today?"
    )
    result = pass_gate(response)
    
    print(f"  ok: {result.ok}")
    print(f"  repaired: {result.repaired}")
    print(f"  reason: {result.reason}")
    print(f"  m-level: {result.meta.get('m')}")
    print()


def example_2_missing_marker():
    """Missing compliance marker → auto-repaired."""
    print("=" * 60)
    print("Example 2: Missing compliance marker → auto-repair")
    print("=" * 60)
    
    response = "I'll help you with that task."
    result = pass_gate(response)
    
    print(f"  ok: {result.ok}")
    print(f"  repaired: {result.repaired}")
    print(f"  auto_trigger: {result.auto_trigger}")
    print(f"  reason: {result.reason}")
    print(f"  repaired text (first 80 chars): {result.text[:80]}...")
    print()


def example_3_circuit_breaker():
    """After 3+ auto-corrections, circuit breaker activates."""
    print("=" * 60)
    print("Example 3: Circuit breaker (4th auto-correction)")
    print("=" * 60)
    
    response = "Another unformatted response."
    
    # Simulate: 0th → 1st → 2nd → 3rd → 4th
    for count in range(5):
        result = pass_gate(response, auto_trigger_count=count)
        breaker = "🔥 CIRCUIT BREAKER" if not result.auto_trigger and result.repaired else ""
        print(f"  count={count}: repaired={result.repaired}, "
              f"auto_trigger={result.auto_trigger}, "
              f"reason={result.reason} {breaker}")
    print()


def example_4_custom_pattern():
    """Use a custom compliance pattern."""
    print("=" * 60)
    print("Example 4: Custom compliance pattern")
    print("=" * 60)
    
    # Override with a simpler pattern
    set_pattern(
        pattern=r'\[OK:(?P<m>\d)\]',
        fix_template="[OK:0] <auto-repaired>"
    )
    
    response = "[OK:2] This uses a custom marker format."
    m = extract_m(response)
    print(f"  extracted m-level: {m}")
    
    result = pass_gate(response)
    print(f"  ok: {result.ok}")
    print(f"  repaired: {result.repaired}")
    print()


def example_5_stdin_mode():
    """Demonstrate stdin pipe mode."""
    print("=" * 60)
    print("Example 5: stdin pipe mode (echo | python -m src.gate)")
    print("=" * 60)
    print("  Usage: echo 'your text' | python -m src.gate")
    print()


if __name__ == "__main__":
    example_1_clean_pass()
    example_2_missing_marker()
    example_3_circuit_breaker()
    example_4_custom_pattern()
    example_5_stdin_mode()
