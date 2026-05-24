"""
Agent Governance Framework — Gate Module v2.0 (信 / Railway Signal)

Four-layer railway signal system for AI agents.
pass_gate() is the core function: signal check + track check, zero tolerance.
No auto-repair — the agent must self-correct.

Protocol:
  Pre-Gate:  station entry authorization
  In-Gate:   tool proxy capability gating  
  Post-Gate: station exit contract (output schema validation)
  Final-Gate: endpoint delivery compliance

The agent is the train. The gate is the signal light. The harness is the control tower.
"""

import re
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── Pattern Configuration ──
_DEFAULT_PATTERN = r'###\s*Task[：:].*→?\s*M(?P<m>\d)'
_M_RE = re.compile(_DEFAULT_PATTERN, re.UNICODE)

def set_pattern(pattern: str):
    """Override the default compliance pattern."""
    global _M_RE
    if "(?P<m>" not in pattern:
        pattern = re.sub(r'M\\d', r'M(?P<m>\\d)', pattern, count=1)
    _M_RE = re.compile(pattern, re.UNICODE)

# ── Signal Layer: Encoding Line + Panel ──
def has_panel(text: str) -> bool:
    """Check if text contains a dispatch panel (box-drawing borders)."""
    lines = text.split('\n')
    has_top = has_bottom = has_content = False
    for line in lines:
        if '┌' in line and '┐' in line: has_top = True
        elif '└' in line and '┘' in line: has_bottom = True
        elif '│' in line and line.strip().startswith('│'): has_content = True
    return has_top and has_bottom and has_content

def extract_m(text: str) -> int | None:
    """Extract the M-level from the first line. Returns None if missing."""
    first_line = text.strip().split('\n')[0]
    m = _M_RE.search(first_line)
    if m:
        try: return int(m.group("m"))
        except: return None
    return None

def has_compliance_marker(text: str) -> bool:
    return extract_m(text) is not None

# ── Track Layer: Station Schema Validation ──
class StationSchema:
    def __init__(self, name: str, state: str,
                 required_fields: List[str] = None,
                 required_patterns: List[str] = None,
                 forbidden_patterns: List[str] = None):
        self.name = name; self.state = state
        self.required_fields = required_fields or []
        self.required_patterns = required_patterns or []
        self.forbidden_patterns = forbidden_patterns or []

_STATIONS: Dict[str, StationSchema] = {}

def register_station(name: str, state: str,
                     required_fields: List[str] = None,
                     required_patterns: List[str] = None,
                     forbidden_patterns: List[str] = None):
    """Register a pipeline station with its output schema."""
    _STATIONS[name] = StationSchema(name, state, required_fields, required_patterns, forbidden_patterns)

def check_track(station: str, text: str) -> Dict[str, Any]:
    """Validate output against station schema."""
    st = _STATIONS.get(station)
    if not st:
        return {"ok": False, "station": station, "error": f"Unknown: {station}", "missing": [], "violations": []}
    missing = [f for f in st.required_fields if f not in text]
    missing += [p for p in st.required_patterns if not re.search(p, text)]
    violations = [p for p in st.forbidden_patterns if re.search(p, text)]
    return {"ok": len(missing)==0 and len(violations)==0, "station": station, "state": st.state, "missing": missing, "violations": violations}

# ── Interception Logging ──
_LOG_FILE = os.path.join(os.path.dirname(__file__) or ".", "gate-interceptions.jsonl")

def set_log_path(path: str):
    global _LOG_FILE; _LOG_FILE = path

def _log_interception(reason: str, station: Optional[str], text_snippet: str):
    os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(), "reason": reason, "station": station or "free", "snippet": text_snippet[:100]}, ensure_ascii=False) + "\n")
    except: pass

def get_interception_stats() -> Dict[str, Any]:
    if not os.path.exists(_LOG_FILE): return {"total": 0, "by_reason": {}, "by_station": {}, "recent": []}
    by_reason, by_station, recent, total = {}, {}, [], 0
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try: e = json.loads(line)
                except: continue
                total += 1
                r, s = e.get("reason","?"), e.get("station","?")
                by_reason[r] = by_reason.get(r,0)+1
                by_station[s] = by_station.get(s,0)+1
                recent.append(e)
    except: pass
    return {"total": total, "by_reason": dict(sorted(by_reason.items(), key=lambda x:-x[1])), "by_station": dict(sorted(by_station.items(), key=lambda x:-x[1])), "recent": recent[-10:]}

# ═══════════════════════════════════════════
# GateResult + pass_gate v2.0
# ═══════════════════════════════════════════

@dataclass
class GateResult:
    """Result of gate check. Compatible with bool() and tuple unpacking."""
    ok: bool; reason: str = "ok"; text: str = ""; meta: Dict[str, Any] = field(default_factory=dict)
    repaired: bool = False; auto_trigger: bool = False; forced: bool = False; trigger_reason: str = ""
    def __bool__(self): return self.ok
    def __iter__(self): return iter((self.ok, self.reason))

def pass_gate(text: str, station: Optional[str] = None) -> GateResult:
    """
    Railway Signal Gate v2.0 — signal + track dual check, zero tolerance.

    Signal check: encoding line + panel (for M1+)
    Track check: station output schema (when station is specified)

    No auto-repair. The gate only signals STOP or GO.
    """
    if not text or not text.strip():
        _log_interception("empty-output", station, "")
        return GateResult(ok=False, reason="empty-output", text="")
    m = extract_m(text)
    if m is None:
        _log_interception("missing-code", station, text[:100])
        return GateResult(ok=False, reason="missing-code", text=text[:200])
    if m == 0: signal_ok = True
    elif has_panel(text): signal_ok = True
    else:
        _log_interception("missing-panel", station, text[:100])
        return GateResult(ok=False, reason="missing-panel", text=text[:200], meta={"m": m})
    if station:
        track = check_track(station, text)
        if not track["ok"]:
            parts = []
            if track.get("missing"): parts.append(f"missing={track['missing']}")
            if track.get("violations"): parts.append(f"violations={track['violations']}")
            reason = "track:" + " + ".join(parts)
            _log_interception(reason[:80], station, text[:100])
            return GateResult(ok=False, reason=reason[:200], text=text[:200], meta={**track, "m": m})
    return GateResult(ok=True, reason="ok-m0" if m==0 else "ok", text=text, meta={"m": m})

# ── Self-test ──
if __name__ == "__main__":
    register_station("describer", "DESCRIBED", required_fields=["user_verbatim", "core_intent", "acceptance_criteria"])
    print("=== Signal ===")
    for label, t in [("missing-code","OK."), ("M0-pass","### Task: R0-C0 → M0 | tag:t | gate:N\nOK."), ("M1-no-panel","### Task: R1-C2 → M1 | tag:t | gate:N\nNo panel..."), ("M1+panel","### Task: R1-C2 → M1 | tag:t | gate:N\n┌──┐\n│OK│\n└──┘\nBody")]:
        r = pass_gate(t); print(f"  {label}: ok={r.ok}")
    print("=== Track ===")
    ok_t = "### Task: R1-C1 → M1 | tag:t | gate:N\n┌──┐\n│OK│\n└──┘\nuser_verbatim: t\ncore_intent: t\nacceptance_criteria: t"
    bad_t = "### Task: R1-C1 → M1 | tag:t | gate:N\n┌──┐\n│OK│\n└──┘\nrandom..."
    print(f"  valid: ok={pass_gate(ok_t, station='describer').ok}")
    print(f"  invalid: ok={pass_gate(bad_t, station='describer').ok}")
    print(f"  free-mode: ok={pass_gate(bad_t, station=None).ok}")
    print(f"  stats: {get_interception_stats()['total']} interceptions")
