# Agent Governance Framework

> **Railway Signal System for AI Agents — gate, guard, govern.**

A lightweight control plane for agent safety, permission management, pipeline orchestration, and semantic drift detection. Built on the principle that **agents should be controlled, not trusted.**

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
from src.gate import pass_gate

# Agent generates a response
response = "I'll help you with that."

# Run it through the gate
result = pass_gate(response)

if result.repaired:
    print("⚠️ Response was auto-corrected by gate")
    response = result.text

print(response)
```

### GateResult

```python
@dataclass
class GateResult:
    ok: bool               # Did it pass?
    repaired: bool          # Was it auto-fixed?
    auto_trigger: bool      # Should agent self-correct?
    trigger_reason: str     # Why was it triggered?
    reason: str             # Human-readable reason
    text: str               # The (possibly repaired) text
```

### Circuit Breaker

After 3 consecutive auto-corrections, the circuit breaker activates — the gate still repairs output but stops triggering self-correction loops.

---

## Architecture

| Component | Description | Status |
|-----------|-------------|--------|
| **Gate** (`src/gate.py`) | Pass/fail check + auto-repair + circuit breaker | ✅ Stable |
| **Pipeline FSM** | State machine for multi-stage agent workflows | 🚧 In Progress |
| **Tool Proxy** | Permission-gated tool execution | 🚧 In Progress |
| **Review Recursion** | Multi-level quality audit (1-review → 3-review → Roundtable) | 🚧 In Progress |
| **Semantic Drift Detection** | Detect when agent subtly changes user intent | 🚧 In Progress |

---

## Philosophy

> *"Never trust an LLM's spontaneity. Process control must be externalized in code. The LLM is just a replaceable text generator inside the process."*

This framework is built on a simple premise: **the agent is the controlled object, not the controller.** The harness (control plane) holds all authority. The agent runs on rails.

### Core Principles

- **80% static rules, 20% LLM judgment** — Don't build another agent to check agents
- **Fail at the section, not the whole line** — Railway signaling: if a train fails at one section, retry only that section
- **Form compliance ≠ substance compliance** — A format check is not a quality guarantee
- **The harness, not the agent, owns all five powers**

---

## Installation

```bash
pip install agent-governance-framework
# or
git clone https://github.com/luts36/agent-governance-framework.git
cd agent-governance-framework
pip install -e .
```

## Requirements

- Python 3.10+
- No external dependencies (stdlib only for core gate)

---

## Project Structure

```
agent-governance-framework/
├── README.md              # You're here
├── LICENSE                # MIT
├── src/
│   └── gate.py            # Core gate function (pass_gate, GateResult)
├── docs/
│   └── railway-signal-system.md  # The theory behind the system
└── examples/
    └── basic_usage.py     # Quick examples
```

---

## Who Is This For?

- **AI/ML engineers** deploying agents to production
- **Platform teams** building agent infrastructure
- **Security engineers** concerned about agent behavior
- **Researchers** exploring AI alignment and control

If you're building with LangGraph, CrewAI, AutoGen, or any agent framework — this adds the **control layer** they're missing.

---

## Comparison

| Framework | Focus | Governance? | Permissions? | Drift Detection? |
|-----------|-------|:-----------:|:------------:|:----------------:|
| LangGraph | Agent orchestration | ❌ | ❌ | ❌ |
| CrewAI | Role-based agents | ❌ | ❌ | ❌ |
| AutoGen | Multi-agent chat | ❌ | ❌ | ❌ |
| Guardrails AI | Output validation | ⚠️ format only | ❌ | ❌ |
| **AGF (this)** | **Full control plane** | ✅ | ✅ | ✅ |

---

## Status

Early stage. The gate core is stable and production-tested. Pipeline, tool proxy, and review recursion are actively being developed and will be open-sourced as they mature.

**First release focus**: Gate function + Railway Signal System theory.

---

## Contributing

This is a new project in a nascent field. If you're thinking about AI agent safety and control, you're early. Issues and discussions welcome.

## License

MIT — see [LICENSE](LICENSE).
