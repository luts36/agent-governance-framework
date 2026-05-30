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
│                   RAILWAY SIGNAL SYSTEM                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Control Tower (You)                                   │
│        │                                                │
│   ┌────┴────┐                                          │
│   │   CLI   │ ← Your control console                   │
│   └────┬────┘                                          │
│        │                                                │
│   ┌────┴──────────────────────────────────┐            │
│   │              GATE (Signal Lights)      │            │
│   │  Pre-Gate → In-Gate → Post-Gate → Final│           │
│   └────┬──────────────────────────────────┘            │
│        │                                                │
│   ┌────┴────┐                                          │
│   │  AGENT  │ ← The train. Runs on rails you define.   │
│   │ (Train) │   Cannot choose its own track.           │
│   └─────────┘                                          │
│                                                         │
│   The train doesn't control the signals.                │
│   The control tower does.                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Features

**v4.2 — Production Ready**

- **Pure Interception**: Gate blocks non-compliant outputs, logs reasons, suggests fixes
- **Measurement Logging**: Every interception logged with reason, station, timestamp
- **Reminder Language**: "Remind" instead of "punish" — interception is context injection for next turn
- **Station Schemas**: Output validation per pipeline station
- **Auto-Dispatcher**: Fully automated compliance engine (no manual triggers)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Agent Governance Framework                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │    Gate      │    │  Dispatcher  │                  │
│  │  (v4.2)     │    │  (Auto)      │                  │
│  └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                          │
│         ▼                   ▼                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Rules Engine                        │  │
│  │  • Signal checks (encoding lines, panels)        │  │
│  │  • Schema validation (per-station output)        │  │
│  │  • Interception logging                          │  │
│  │  • Auto-remediation suggestions                  │  │
│  └─────────────────────────────────────────────────┘  │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐                                     │
│  │    Agent     │ ← Runs on rails you define          │
│  │   (Train)    │   Cannot choose its own track       │
│  └──────────────┘                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
git clone https://github.com/luts36/agent-governance-framework.git
cd agent-governance-framework
pip install -r requirements.txt
```

### Basic Usage

```python
from src.gate import pass_gate, get_interception_stats

# Check agent output
result = pass_gate(
    "### 任务编码：R1-C2 → M3 | tag:review | gate:Y\n\nTask completed successfully.",
    station="review"
)

if result.passed:
    print("✅ Output compliant")
else:
    print(f"❌ Blocked: {result.reason}")
    print(f"💡 Fix: {result.fix_suggestion}")

# Get interception statistics
stats = get_interception_stats()
print(f"Total interceptions: {stats['total']}")
```

### Auto-Dispatcher

The dispatcher runs automatically, consuming cron job outputs:

```python
from src.dispatcher import Dispatcher

# Initialize dispatcher
dispatcher = Dispatcher()

# Process latest outputs
actions = dispatcher.process()
for action in actions:
    print(f"Action: {action['type']} - {action['message']}")
```

## Gate System (v4.2)

### Four-Layer Gate

```
Pre-Gate → In-Gate → Post-Gate → Final
   │          │          │          │
   ▼          ▼          ▼          ▼
  Entry    Tool Use    Output    Departure
  Check    Permission  Schema    Validation
```

### Signal Checks

| Check | Description | Block Condition |
|-------|-------------|-----------------|
| R0 | Encoding line present | Missing or malformed |
| R1 | Panel visible | Hidden or omitted |
| R2 | Station schema match | Fields mismatch |
| R3 | Interception logged | Repeat violation |

### Interception Logging

Every interception is logged to `~/.agent-governance/logs/gate-interceptions.jsonl`:

```json
{
  "timestamp": "2026-05-30T14:30:00Z",
  "station": "review",
  "reason": "missing_encoding_line",
  "input_hash": "abc123",
  "fix_suggestion": "Add: ### 任务编码：R?-C? → M?"
}
```

## Dispatcher (Auto-Compliance)

The dispatcher consumes outputs from 4 cron jobs and automatically:

- **Compliance Scan**: Checks agent behavior patterns
- **Config Hash**: Detects configuration drift
- **TRCM Audit**: Validates TRCM compliance
- **Friend Log**: Monitors interaction patterns

### Auto-Actions

| Condition | Action |
|-----------|--------|
| Compliance violation | Auto-encode + suggest roundtable |
| Config drift | Alert + rollback suggestion |
| TRCM non-compliance | Block + remediation |
| Pattern anomaly | Log + investigate |

## Configuration

### Environment Variables

```bash
# Rules file location
export AG_RULES_PATH=~/.agent-governance/rules.yaml

# Station schemas
export AG_SCHEMAS_PATH=~/.agent-governance/station-schemas.yaml

# Log directory
export AG_LOG_DIR=~/.agent-governance/logs
```

### Rules File

```yaml
rules:
  R0:
    pattern: "###\\s*任务编码[：:].*→?\\s*M(?P<m>\\d)"
    fix: "### 任务编码：R?-C? → M? | tag:<标签> | gate:Y/N"
  R1:
    require_panel: true
  R2:
    schemas_dir: "station-schemas/"
```

## Ecosystem

This project is part of the **AI Agent Governance** ecosystem:

```
┌─────────────────────────────────────────────────────────┐
│                  AI Agent Governance                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  agent-governance-framework    unified-inertia-theory   │
│  (Process Governance)          (Cognitive Governance)    │
│         │                            │                  │
│         │                            │                  │
│         ▼                            ▼                  │
│  ┌──────────────┐            ┌──────────────┐          │
│  │ Gate System  │            │ Inertia      │          │
│  │ • Signal     │            │ • Detection  │          │
│  │ • Schema     │            │ • Measurement│          │
│  │ • Auto-fix   │            │ • Correction │          │
│  └──────────────┘            └──────────────┘          │
│                                                         │
│  "Did the agent follow        "Is the agent stuck      │
│   the process?"                in a pattern?"           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Related Projects

- **[unified-inertia-theory](https://github.com/luts36/unified-inertia-theory)**: Detect, measure, and correct AI Agent cognitive inertia

## Comparison

| Feature | LangGraph Guardrails | NeMo Guardrails | This Framework |
|---------|---------------------|-----------------|----------------|
| Process enforcement | ❌ | ❌ | ✅ |
| Signal system | ❌ | ❌ | ✅ |
| Auto-dispatcher | ❌ | ❌ | ✅ |
| Schema validation | ❌ | ❌ | ✅ |
| Interception logging | ❌ | ❌ | ✅ |
| Auto-remediation | ❌ | ❌ | ✅ |

## Who is this for?

- **AI Agent developers** building reliable autonomous systems
- **MLOps engineers** monitoring agent behavior in production
- **AI safety teams** establishing behavioral standards
- **Enterprise teams** deploying agents in critical workflows

## Status

**v4.2** — Stable, production-ready

## License

MIT License — see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{agent_governance_framework,
  title={Agent Governance Framework: Railway Signal System for AI Agents},
  author={Agent Governance Framework Team},
  year={2026},
  url={https://github.com/luts36/agent-governance-framework}
}
```
