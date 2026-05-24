# Agent Governance Framework

> **Railway Signal System for AI Agents — gate, guard, govern.**

A lightweight control plane for agent output validation, pipeline orchestration, and semantic drift detection. Built on the principle that **agents should be controlled, not trusted.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## The Problem

AI agents are powerful. They're also unreliable: they hallucinate, drift semantically, skip safety checks, and make unauthorized tool calls.

Existing frameworks (LangGraph, CrewAI, AutoGen) focus on making agents **more capable**. Nobody is focused on making them **more controllable**.

## The Solution: Railway Signal System

We model agent control after railway safety systems — the most reliable human-designed control infrastructure in existence.

```
┌─────────────────────────────────────────────────────────┐
│                   RAILWAY SIGNAL SYSTEM                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Control Tower (You)                                    │
│        │                                                │
│   ┌────┴────┐                                           │
│   │   CLI   │ ← Your control console                    │
│   └────┬────┘                                           │
│        │                                                │
│   ┌────┴──────────────────────────────────┐            │
│   │              GATE (Signal Lights)       │            │
│   │  Pre-Gate → In-Gate → Post-Gate → Final │            │
│   └────┬──────────────────────────────────┘            │
│        │                                                │
│   ┌────┴────┐                                           │
│   │  AGENT  │ ← The train. Runs on rails you define.    │
│   │ (Train) │   Cannot choose its own track.            │
│   └─────────┘                                           │
│                                                         │
│   The train doesn't control the signals.                │
│   The control tower does.                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Five Powers the Agent Does NOT Have

1. ❌ Choose which skill/tool to use
2. ❌ Grant itself permissions
3. ❌ Submit its own state
4. ❌ Call real tools directly
5. ❌ Trigger downstream actions

All five belong to the Harness (control plane). The agent is a train on rails — it only moves when signaled.

---

## Quick Start

```python
from src.gate import pass_gate, register_station, get_interception_stats

# Register a pipeline station with required output fields
register_station("describer", "DESCRIBED",
    required_fields=["user_verbatim", "core_intent", "acceptance_criteria"])

# Agent generates a response
response = "I'll help you with that."

# Run it through the gate (free mode — signal check only)
result = pass_gate(response)
print(result.ok)      # False — missing compliance marker
print(result.reason)  # "missing-code"

# With station context (signal + track dual check)
compliant = """### Task: R1-C1 → M1 | tag:describer | gate:N
┌─────────────────┐
│  Dispatch Panel  │
└─────────────────┘
user_verbatim: sort desktop .md files
core_intent: list .md files sorted by size
acceptance_criteria: terminal outputs sorted file list"""

result = pass_gate(compliant, station="describer")
print(result.ok)  # True — signal + track both pass

# Check interception metrics
stats = get_interception_stats()
print(f"Total interceptions: {stats['total']}")
print(f"By reason: {stats['by_reason']}")
```

### Philosophy: Zero Tolerance

The gate does NOT auto-repair. If a response fails the check, it's intercepted. The agent must self-correct.

Auto-repair creates moral hazard — the agent learns "someone will fix it" and keeps making the same mistake. The gate only signals STOP or GO.

---

## Architecture

### Dual-Check System

| Layer | What it checks | How |
|-------|---------------|-----|
| **Signal** | Encoding line + dispatch panel | Regex pattern match |
| **Track** | Station-specific output fields | Schema validation via `check_track()` |

### Station Schema

Each pipeline station defines its required output format:

```python
register_station("executor", "EXECUTED",
    required_fields=["Step 1:", "Step 2:"],
    forbidden_patterns=[r"rm -rf"])
```

### Components

| Component | Description | Status |
|-----------|-------------|--------|
| **Gate** (`src/gate.py`) | Signal+track dual check, zero tolerance, interception logging | ✅ v2.0 |
| **Pipeline FSM** | 5-station state machine (describer→rater→designer→reviewer→executor) | ✅ Verified |
| **Tool Proxy** | Permission-gated tool execution per station | 🚧 In Progress |
| **Review Recursion** | Multi-level quality audit (1-review → 3-review → Roundtable) | ✅ Built |
| **Semantic Drift Detection** | Detect when agent subtly changes user intent | ✅ Built |

---

## Philosophy

> *"Never trust an LLM's spontaneity. Process control must be externalized in code. The LLM is just a replaceable text generator inside the process."*

### Core Principles

- **Zero tolerance, not auto-repair** — Fixing the agent's mistakes teaches it to keep making them. Intercept and make it self-correct.
- **Dual check: signal + track** — Not just "is the format right?" but "are the right fields present for this station?"
- **80% static rules, 20% LLM judgment** — Don't build another agent to check agents. Regex and schema validation are deterministic.
- **The harness, not the agent, owns all five powers**

---

## Installation

```bash
git clone https://github.com/luts36/agent-governance-framework.git
cd agent-governance-framework
```

No external dependencies — stdlib only.

Requirements: Python 3.10+

---

## Project Structure

```
agent-governance-framework/
├── README.md              # You're here
├── LICENSE                # MIT
├── src/
│   └── gate.py            # Core gate v2.0 (signal+track dual check)
├── docs/
│   └── railway-signal-system.md  # The theory behind the system
└── examples/
    └── basic_usage.py     # Quick examples
```

---

## Comparison

| Framework | Focus | Signal Gate | Track Schema | Drift Detection |
|-----------|-------|:-----------:|:------------:|:----------------:|
| Guardrails AI | Output validation | ✅ | ❌ | ❌ |
| NeMo Guardrails | Conversational rails | ✅ | ❌ | ❌ |
| LangGraph | Agent orchestration | ❌ | ❌ | ❌ |
| CrewAI | Role-based agents | ❌ | ❌ | ❌ |
| **AGF (this)** | **Full control plane** | ✅ | ✅ | ✅ |

---

## Status

**v2.0 (2026-05-24)**: Gate upgraded to signal+track dual check with zero-tolerance interception. Pipeline FSM verified end-to-end. Review recursion and semantic drift detection built and awaiting open-source cleanup.

---

## License

MIT — see [LICENSE](LICENSE).
