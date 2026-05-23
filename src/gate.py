"""
Agent Governance Framework — Gate Module

Railway signal system for AI agents.
pass_gate() is the core function: check, repair, circuit-break.

Protocol:
- Every agent response passes through the gate before delivery.
- Missing format → auto-repaired + marked [gate:auto-corrected]
- >3 consecutive auto-corrections → circuit breaker activates

The agent is the train. The gate is the signal light. The harness is the control tower.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict

# ── Pattern for extracting compliance markers ──
# Default: looks for "### Task: R?-C? → M?" style markers
_DEFAULT_PATTERN = r'###\s*Task[：:].*→?\s*M(?P<m>\d)'
_DEFAULT_FIX = "### Task: R?-C? → M? | tag:system | gate:N"

_M_RE = re.compile(_DEFAULT_PATTERN, re.UNICODE)


def set_pattern(pattern: str, fix_template: str = None):
    """Override the default compliance pattern and fix template."""
    global _M_RE, _DEFAULT_FIX
    if "(?P<m>" not in pattern:
        pattern = re.sub(r'M\\d', r'M(?P<m>\\d)', pattern, count=1)
    _M_RE = re.compile(pattern, re.UNICODE)
    if fix_template:
        _DEFAULT_FIX = fix_template


# ── Panel detection (box-drawing characters) ──
def has_panel(text: str) -> bool:
    """Check if text contains a dispatch panel (box-drawing borders)."""
    lines = text.split('\n')
    has_top = has_bottom = has_content = False
    for line in lines:
        if '┌' in line and '┐' in line:
            has_top = True
        elif '└' in line and '┘' in line:
            has_bottom = True
        elif '│' in line and line.strip().startswith('│'):
            has_content = True
    return has_top and has_bottom and has_content


def extract_m(text: str) -> int | None:
    """Extract the M-level from the first line. Returns None if missing."""
    first_line = text.strip().split('\n')[0]
    m = _M_RE.search(first_line)
    if m:
        try:
            return int(m.group("m"))
        except (IndexError, ValueError):
            return None
    return None


def has_compliance_marker(text: str) -> bool:
    """Check if the first line has a compliance marker."""
    return extract_m(text) is not None


# ═══════════════════════════════════════════
# GateResult + pass_gate
# ═══════════════════════════════════════════

@dataclass
class GateResult:
    """Result of gate check. Compatible with bool() and tuple unpacking."""
    ok: bool
    repaired: bool = False
    forced: bool = False
    auto_trigger: bool = False        # Agent should load correction skill
    trigger_reason: str = ""          # "missing-marker" / "missing-panel"
    reason: str = "ok"
    text: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self):
        return self.ok

    def __iter__(self):
        """Compatible with (bool, str) tuple unpacking."""
        return iter((self.ok, self.reason))


def _make_compliance_line(m: int = 0, forced: bool = False) -> str:
    """Generate a compliance marker line."""
    tag = "auto-corrected" if forced else "system"
    gate = "Y" if forced else "N"
    tmpl = _DEFAULT_FIX
    try:
        return (tmpl
                .replace("<标签>", tag)
                .replace("Y/N", gate)
                .replace("R?-C?", f"R1-C{min(m, 3)}")
                .replace("M?", f"M{m}"))
    except Exception:
        return f"### Task: R1-C{min(m, 3)} → M{m} | tag:{tag} | gate:{gate}"


def _make_minimal_panel() -> str:
    """Generate a minimal system correction panel."""
    return (
        "┌─────────────────────────────────────────┐\n"
        "│  ⚠ System Correction: format non-compliant  │\n"
        "│  Auto-repaired by gate                       │\n"
        "└─────────────────────────────────────────┘"
    )


def _repair_text(text: str, missing_marker: bool, missing_panel: bool, m_level: int) -> str:
    """Repair text: add compliance marker + optional panel."""
    lines = text.strip().split('\n')

    if missing_marker:
        marker = _make_compliance_line(m=m_level, forced=True)
        body = text.strip()
        if lines and not _M_RE.search(lines[0]):
            body = '\n'.join(lines)
        result = marker + '\n' + body
    else:
        result = text.strip()

    if missing_panel and m_level >= 1:
        idx = result.index('\n') if '\n' in result else len(result)
        result = result[:idx + 1] + '\n' + _make_minimal_panel() + '\n' + result[idx + 1:]

    return result


def pass_gate(text: str, auto_trigger_count: int = 0) -> GateResult:
    """
    Railway signal gate — check, repair, circuit-break.

    Args:
        text: The agent's response text to check.
        auto_trigger_count: Consecutive auto-correction count (for circuit breaker).

    Returns:
        GateResult:
        - ok=True, repaired=False: passed clean
        - ok=True, repaired=True, auto_trigger=True: auto-repaired (agent should self-correct)
        - ok=True, repaired=True, auto_trigger=False: circuit breaker active (repair only)
    """
    circuit_breaker = auto_trigger_count > 3

    if not text or not text.strip():
        repaired = _repair_text("", missing_marker=True, missing_panel=True, m_level=0)
        return GateResult(
            ok=True, repaired=True, forced=True,
            auto_trigger=not circuit_breaker,
            trigger_reason="empty-output" if not circuit_breaker else "",
            reason="circuit-breaker:empty" if circuit_breaker else "empty-output-repaired",
            text=repaired,
            meta={"original": "", "auto_trigger_count": auto_trigger_count}
        )

    m = extract_m(text)

    # Case 1: Missing compliance marker
    if m is None:
        repaired = _repair_text(text, missing_marker=True,
                                missing_panel=not has_panel(text), m_level=1)
        return GateResult(
            ok=True, repaired=True, forced=True,
            auto_trigger=not circuit_breaker,
            trigger_reason="missing-marker" if not circuit_breaker else "",
            reason="circuit-breaker:missing-marker" if circuit_breaker else "missing-marker-auto-corrected",
            text=repaired,
            meta={"original": text[:200], "auto_trigger_count": auto_trigger_count}
        )

    # Case 2: Has marker, M0 — pass
    if m == 0:
        return GateResult(ok=True, reason="ok-m0", text=text, meta={"m": 0})

    # Case 3: Has marker, M1+, has panel — pass
    if has_panel(text):
        return GateResult(ok=True, reason="ok", text=text, meta={"m": m})

    # Case 4: Has marker, M1+, missing panel
    repaired = _repair_text(text, missing_marker=False, missing_panel=True, m_level=m)
    return GateResult(
        ok=True, repaired=True, forced=True,
        auto_trigger=not circuit_breaker,
        trigger_reason="missing-panel" if not circuit_breaker else "",
        reason="circuit-breaker:missing-panel" if circuit_breaker else "missing-panel-auto-corrected",
        text=repaired,
        meta={"m": m, "original": text[:200], "auto_trigger_count": auto_trigger_count}
    )


# ── CLI entry point ──
if __name__ == "__main__":
    import sys
    src = sys.stdin.read()
    result = pass_gate(src)
    print(result.text if result.ok else src)
