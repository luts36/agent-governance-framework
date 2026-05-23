# Railway Signal System — The Core Model

> The theoretical foundation of Agent Governance Framework.

## Why Railways?

Railway signaling is the most reliable human-designed control infrastructure. Trains have been running safely for over 150 years on a simple principle: **the train doesn't control the signals — the control tower does.**

AI agents are trains. They're powerful but dangerous if allowed to choose their own track. The solution is not to make trains smarter. It's to build better signals.

## Core Mapping

| Railway | Harness | Controlled By | Description |
|---------|---------|:------------:|-------------|
| Control Tower | **You** | You | Ultimate authority |
| Track Diagram | State Machine (FSM) | Your design | Defines all legal tracks and stations |
| Control Console | CLI | You | `/pipeline` commands, progress panels |
| Entry Signal | Pre-Gate | Harness | Conditions not met → signal stays red |
| Track Token | Capability | Harness | Temporary pass issued by control |
| Switch | Tool Proxy | Harness | Agent never touches real tracks |
| Exit Signal | Post-Gate | Harness | Output invalid → state not committed |
| Train | **Agent** | Controlled object | Moves only within current section |
| Section | Current Skill | Harness-assigned | Train sees only current track segment |
| Interlocking | Chain Trigger | Harness via FSM | Train doesn't throw its own switches |
| Emergency Brake | Ctrl+C / Approval | You | Stop at any section, anytime |
| Black Box | Audit Log | Harness | Every section recorded |

## Five Powers the Agent Must Never Have

1. **Choose skills** — The harness assigns. The agent receives.
2. **Grant permissions** — Permissions are pre-configured, not negotiated.
3. **Submit state** — Only the harness commits state transitions.
4. **Call real tools** — All tool calls go through Tool Proxy.
5. **Trigger downstream** — Only the harness initiates next steps.

## The Gate: Four-Layer Signal

The Gate (originally "信" — Chinese for both "signal" and "trust/credential") operates at four levels:

```
┌──────────────────────────────────────────────────┐
│                  FOUR-LAYER GATE                    │
├──────────────────────────────────────────────────┤
│                                                    │
│  Pre-Gate (Entry)                                  │
│  ├─ Is the skill allowed?                          │
│  ├─ Does input match schema?                       │
│  └─ Is budget within limits?                       │
│                                                    │
│  In-Gate (Execution)                               │
│  ├─ Is the tool in the allowlist?                  │
│  ├─ Are parameters within bounds?                  │
│  └─ Is this a cross-skill call?                    │
│                                                    │
│  Post-Gate (Exit)                                  │
│  ├─ Does output match schema?                      │
│  ├─ Can the downstream station consume this?       │
│  └─ Is the artifact valid?                         │
│                                                    │
│  Final-Gate (Delivery)                             │
│  ├─ Is this clear to the user?                     │
│  ├─ Does it leak internal state?                   │
│  └─ Does it claim "done" when unfinished?          │
│                                                    │
└──────────────────────────────────────────────────┘
```

## Design Principle: 80/20 Rule

**80% static rules, 20% LLM judgment.**

The gate is not another agent. Most checks are mechanical:
- Regex pattern matching
- Schema validation
- Allowlist lookups
- State machine transitions

Reserve LLM judgment for genuinely ambiguous cases — semantic drift detection, quality assessment, context-aware decisions.

## Why Not Just Prompt Engineering?

Prompts are suggestions. Agents ignore suggestions.

A gate is a hard constraint. The response doesn't reach the user until the gate clears it. This is the difference between "please don't" and "you can't."

## Token Efficiency

**Old model (post-hoc review):** Agent runs → makes mistake → re-run entire workflow. ~50% token waste.

**Railway model (per-section gating):** Agent runs one section → gate checks → pass or retry only that section. ~79% token savings.

## The Name "Gate" (信)

The Chinese character 信 means both "signal" (as in railway signal lights) and "credential/trust" (as in a token of completion). The dual meaning is intentional:

- **Signal** — The gate is a traffic light. Red means stop. Green means go.
- **Credential** — Passing the gate produces a verifiable token that this section was completed correctly.

## Anti-Patterns

| Don't | Do |
|-------|-----|
| Let the agent choose its own M-level | Compute M-level mechanically from task schema |
| Build the gate as another agent | Build the gate as static rules + minimal LLM |
| Trust format compliance as quality | Verify substance, not just format |
| Gate → agent → self-correct loop | Gate → harness rejects → harness requests re-generation |

## References

- [Harness Engineering Research Report](docs/harness-engineering.md) (coming soon)
- [Pass Gate Implementation](src/gate.py)
