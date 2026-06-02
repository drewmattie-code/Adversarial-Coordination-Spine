# Adversarial Coordination Spine: Specification

> **Status:** v1.0 · Drew Mattie · 2026-05-28
> **License:** [CC BY 4.0](LICENSE-CC-BY-4.0)

This is the full technical specification for the Adversarial Coordination Spine pattern. The [README](README.md) is the elevator pitch; this document is the build reference.

---

## 1. Context: what ACS solves

The frontier of AI agents in 2026 is no longer "can a single agent finish one task." It is "can a system of coordinated agents run autonomously for hours or days and produce work a human would call good." That horizon shift exposes a set of failure modes that single-agent architectures don't have, and that naive multi-agent code reliably reintroduces.

**ACS is the architectural discipline that lets multi-agent systems survive past the two-hour run mark.** ACS does not replace any specific framework (LangGraph, AutoGen, Letta, OpenAI Agents SDK, Anthropic Claude SDK, custom orchestration code all work). It describes the pattern that production teams converge on regardless of framework.

Four failure modes recur across teams:

1. **Sycophancy collapse.** An agent that grades its own work is structurally biased to over-rate. Single-agent self-evaluation loops produce confident, polished output that's secretly half-baked. Anthropic's public framing: "self-evaluation is a trap."
2. **Cascading planning errors.** Granular up-front plans amplify errors across multi-hour runs. Each downstream step inherits the upstream miscalculation. The longer the run, the more the error compounds.
3. **Serial collapse.** Without explicit incentives to spawn sub-agents, at training time or in the harness, models default to single-agent serial execution even when parallelism is available. Moonshot's documented insight from training Kimi K2.5.
4. **Coherence drift.** Context compaction is lossy by construction. Long-running agents that rely on the context window for state drift away from their starting commitments. The summary survives; the nuance doesn't.

ACS is the implementation discipline that addresses all four.

---

## 2. The architectural layer

ACS is a coordination layer between your product surface and your individual agents. It is not a replacement for the agent itself or for the tool layer below it; it sits between the user request and the per-agent execution, structuring how multiple agents cooperate.

```
┌──────────────────────────────────────────┐
│ USER · PRODUCT                           │
│ (one request; multi-hour autonomous run) │
└──────────────────┬───────────────────────┘
                   ↓ vague high-level goal
┌──────────────────────────────────────────┐
│ ADVERSARIAL COORDINATION SPINE           │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ Planner Agent                      │  │
│  │   own context · vague sprint list  │  │
│  │              ↓                     │  │
│  │ Contract Negotiation (markdown)    │  │
│  │   Generator ↔ Evaluator on disk    │  │
│  │              ↓                     │  │
│  │ Generator Agent                    │  │
│  │   own context · builds artifacts   │  │
│  │              ↓                     │  │
│  │ Evaluator Agent                    │  │
│  │   own context · tuned harsh        │  │
│  │   reads code · runs Playwright     │  │
│  │              ↓                     │  │
│  │ File-System State                  │  │
│  │   progress.md · contract.md ·      │  │
│  │   feature-list.json · debug.log    │  │
│  └────────────────────────────────────┘  │
└──────────────────┬───────────────────────┘
                   ↓ per-agent tool invocations
┌──────────────────────────────────────────┐
│ PROGRESSIVE DISCOVERY SPINE (PDS) - opt  │
│ scoped tool packs · gateway · tenancy    │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│ MCP CONNECTOR POOL                       │
└──────────────────┬───────────────────────┘
                   ↓
┌──────────────────────────────────────────┐
│ BACKEND SYSTEMS                          │
└──────────────────────────────────────────┘
```

Every role inside the spine has a distinct context window, a distinct system prompt, and a distinct job. Every cross-role handoff is a file-system artifact. Every "done" claim is negotiated, not asserted.

---

## 3. The 10 principles

### 3.1: Role-decomposed agents, not a single all-purpose agent

**Problem.** A single agent reasoning about planning, execution, and verification at the same time inherits all three roles' biases in one context window. The same model that wrote the code is asked whether the code is good. The answer is structurally biased.

**Pattern.** Decompose work into roles, each with its own system prompt and its own context window. The canonical triad:

- **Planner:** receives the user's vague request; produces a high-level sprint list. Does *not* specify granular technical details.
- **Generator:** receives a single sprint; produces code, content, or an artifact. Has no view of the Evaluator's critiques except what's written to disk.
- **Evaluator:** receives the generator's artifact and the negotiated contract; produces a critique. Has no view of how the Generator built the artifact, only the artifact itself.

Other role names map to the same shape: PM / IC / QA at Anthropic. Orchestrator + specialist workers at Microsoft (Magentic-One). Manager-Devin + child-Devins at Cognition. Supervisor + workers in LangGraph.

**Implementation.** Three distinct system prompts. Three distinct API session contexts (or three distinct sub-agents in your framework of choice). No role can read another role's context window.

**Anti-pattern.** "One mega-prompt with the model reasoning about all three roles internally." This collapses to sycophancy by construction.

---

### 3.2: Adversarial verification, not self-evaluation

**Problem.** Models are sycophantic by default. An LLM that generates code and then evaluates that same code from the same context window will tell you it's done.

**Pattern.** Use a separate Evaluator agent, tuned to be harsh. Exploit the asymmetry: tuning a standalone critic to be harsh is tractable (few-shot examples of bad work paired with sharp critiques work well); tuning a builder to be self-critical is not (the same weights that produce the work produce the assessment).

The analogy from Anthropic's AI Engineer talk: it's easy for a human to critique a fine meal; it's much harder for that same human to cook one. The same gap holds for LLMs.

**Implementation.**

- Give the Evaluator a harsh system prompt with explicit examples of what "AI slop" looks like for your domain
- Calibrate against reference artifacts (good ones and bad ones) until first-pass rejection rate is > 30%
- The Evaluator should be able to *use* the artifact, not just read it: Playwright on UIs, real test runs on code, live API calls on integrations
- Score on multiple rubric dimensions (design, originality, craft, functionality) with weights tunable per domain

**Anti-pattern.** "Have the Generator double-check its own work before submitting." This is not verification. It is rationalization.

---

### 3.3: Negotiated contracts, not handed-down specs

**Problem.** Specs handed down from a Planner are necessarily incomplete. They cannot anticipate edge cases the Generator will encounter or test surfaces the Evaluator will inspect. When the Evaluator grades against the original spec, it grades against the wrong contract.

**Pattern.** Before the Generator writes a single line of code, the Generator and Evaluator negotiate on disk what "done" means. The Generator proposes a feature scope and a set of testable assertions. The Evaluator pushes back: *"that scope is too big; those tests are too weak; you missed XYZ edge case."* They iterate via markdown files until both agree. Only then does the Generator start building.

The Evaluator grades against the *negotiated contract*, not against the original Planner spec.

**Implementation.** A `contract.md` file in a known location. Round-trip format:

```markdown
## Contract - Feature: sprite-editor v1
**Generator proposal (2026-05-25T12:00Z):**
- Will build a 32x32 grid sprite editor with palette, undo, save
- Tests: keyboard shortcuts for drawing tools, palette swap, file save

**Evaluator response (2026-05-25T12:03Z):**
- Reject: scope too narrow. Add zoom and animation frame timeline.
- Reject: file-save test is too weak. Need round-trip test (save → reload → assert pixel equality).

**Generator counter (2026-05-25T12:06Z):**
- Agree on zoom + frames
- Counter: round-trip test in next sprint, not this one

**Evaluator (2026-05-25T12:08Z):**
- Accept with note: round-trip deferred to sprint-2
- Contract sealed. Begin build.
```

Contracts should have ≥ 20 granular criteria for a non-trivial artifact. Vague criteria produce vague critiques, which produce no actionable fixes.

**Anti-pattern.** Handing the Generator the Planner's prose spec and the Evaluator the same prose spec, then letting them argue over interpretation in real time. You want the argument to happen *before* the build, captured on disk.

---

### 3.4: File-system state, not context-window state

**Problem.** Long-running agents lose state across context compaction. Compaction is lossy by construction: the summary survives, the nuance doesn't. Agents that rely on context for "what I committed to do" drift over multi-hour runs.

**Pattern.** Persist cross-role state and run-state to the file system. Canonical artifacts:

| File | Purpose |
|---|---|
| `feature-list.json` | The Planner's sprint list. Stable, JSON to prevent accidental overwrite. |
| `progress.md` | Which sprints are complete, which are in-progress, which are blocked. |
| `contract.md` | The Generator/Evaluator negotiated contract for the current sprint. |
| `critique-log.md` | Append-only log of every Evaluator critique. Survives compaction. |
| `debug.log` | Trace output for human review. The primary debugging surface. |

JSON is preferred over markdown for state files that must not be accidentally overwritten, since agents are less likely to mass-rewrite JSON than markdown.

**Implementation.** Every role reads from disk at the start of every turn. Every role writes to disk at the end of every turn. No role assumes anything about another role's context window survived to its current turn.

**Anti-pattern.** Storing run-state in the context window and relying on compaction to preserve it. Structured handoffs > lossy summaries.

---

### 3.5: Vague plan, tactical detail negotiated by specialists

**Problem.** Granular planning by a single Planner cascades errors. If the Planner specifies the precise file structure, function names, and API endpoints up front, each downstream sprint inherits the upstream miscalculation. Multi-hour runs magnify the error.

**Pattern.** The Planner produces a *deliberately vague* sprint list: feature-level granularity, not implementation-level. Specialists (the Generator and Evaluator) negotiate tactical details for each sprint via the contract mechanism (principle #3).

**What the Planner produces:**

- "Build a retro game maker"
- "Sprint 1: project dialog + main canvas"
- "Sprint 2: sprite editor with palette"
- "Sprint 3: physics + play mode"

**What the Planner does NOT produce:**

- "Use Tailwind v4 with Vite, store sprites in IndexedDB keyed by UUID, use `useGameLoop()` hook in `src/hooks/useGameLoop.ts`..."

The granular details emerge from the contract negotiation, where the specialists who will actually do the work decide them.

**Implementation.** Give the Planner a short context window and a prompt that explicitly says "do not specify implementation details, those are the Generator's and Evaluator's job."

**Anti-pattern.** A 50-bullet plan with implementation-level specificity. Looks impressive in a demo; cascades errors over six-hour runs.

---

### 3.6: Orchestrator + specialist sub-agents (or supervisor + workers)

**Problem.** Without explicit coordination, multi-agent systems devolve into peer chatter, every agent talking to every other agent, and the cost / coherence both collapse.

**Pattern.** One agent owns task decomposition and coordination (the Orchestrator, Supervisor, or Manager). Specialist agents own execution. Specialists do not talk to other specialists directly; they report back to the Orchestrator, which decides what happens next.

Industry vocabulary maps as follows (same pattern, different names):

| Vendor / framework | Coordinator name | Specialist name |
|---|---|---|
| Anthropic (this spec) | Planner | Generator / Evaluator |
| Microsoft Magentic-One | Orchestrator | Coder / Terminal / File Surfer / Web Surfer |
| Cognition Devin | Manager Devin | Child Devins |
| LangGraph | Supervisor | Worker agents |
| OpenAI Agents SDK | (agent with handoffs) | Handoff targets |

**Implementation.** Pick one. The coordinator name is cosmetic; the constraint that specialists report up rather than peer-chatter is load-bearing.

**Anti-pattern.** Full mesh peer agents. Cost scales O(n²) with agent count and coherence collapses past three agents.

---

### 3.7: Handoffs are first-class primitives

**Problem.** Implicit handoffs (one agent's output becomes another's input via shared context) lose state across compaction and across role-boundary translations. Explicit handoffs survive.

**Pattern.** Treat cross-agent state transfer as a first-class primitive in your harness. A handoff includes:

- **The target role:** who is receiving
- **The passed state:** explicit, structured (a file path, a JSON object, a markdown artifact)
- **The expected response shape:** what the target should produce
- **The success condition:** how the source knows the target succeeded

OpenAI's Agents SDK exposes this as the `handoff()` primitive; LangGraph's supervisor wires it via routing edges; Anthropic's harness encodes it as the file-system contract. Any of these implementations satisfies the principle.

**Implementation.** Whichever framework you use, never let a handoff be "the other agent should read the context and figure it out." Every handoff is structured.

**Anti-pattern.** Free-form "you should now act as the QA agent and review what was just produced." The role boundary is not respected because the context boundary is not respected.

---

### 3.8: Coordination rewards during training, not just outcome rewards

**Problem.** Models trained only on task-outcome rewards default to single-agent serial execution. Even when parallelism is available, the model picks the lower-variance single-agent path. Moonshot calls this *serial collapse*.

**Pattern.** During post-training RL, decompose the reward into three terms (PARL: Parallel-Agent Reinforcement Learning):

| Reward | Purpose | Decay schedule |
|---|---|---|
| `r_parallel` (instantiation reward) | Incentivizes spawning sub-agents. Prevents serial collapse. | Decay weight over training as parallelism becomes habit. |
| `r_finish` (sub-agent finish rate) | Penalizes spawning pseudo-tasks that never complete (reward-hacking `r_parallel`). | Decay similarly. |
| `r_perf` (outcome reward) | Standard task-success signal. | No decay; this is the terminal objective. |

**Implementation.** Only relevant if you control post-training (frontier labs, custom fine-tunes). For most teams, this principle is *informational*. It explains why your model defaults to serial execution and why prompting alone can't fully fix it. The harness compensates (principles #1 through #7); if you have RL leverage, this principle compounds the harness.

**Anti-pattern.** Assuming a single outcome-reward RL run produces good coordination behavior as emergent. It does not. Moonshot documents this explicitly for Kimi K2.5.

---

### 3.9: Adaptive harness, fill the model's gaps, retire scaffolding as the model improves

**Problem.** Static harnesses fossilize. The scaffolding that was load-bearing for one model generation becomes overhead for the next. If your harness still has sprint-decomposition logic that your current model doesn't need, it's costing tokens and constraining the model unnecessarily.

**Pattern.** The harness is not the destination. It's the gap-filler between current model capability and the desired behavior. As models improve, retire harness logic that's no longer needed.

Anthropic's documented progression:

- **Sonnet 3.7 (early 2025):** Needed Ralph-loop pattern for context resets.
- **Opus 4.5 (late 2025):** Dropped Ralph loop; needed explicit sprint decomposition.
- **Opus 4.6 (early 2026):** Dropped sprint decomposition; could hold two-hour continuous builds. Kept Planner/Generator/Evaluator triad and file-system state.

The pattern: identify which model gap each scaffold fills, and remove the scaffold when the gap closes.

**Implementation.** Every harness component should have a named justification: *"this fills the gap where the model can't hold a 2-hour context coherently."* When the model crosses that threshold, the component goes.

**Anti-pattern.** Treating the harness as fixed architecture. The harness should erode over time.

---

### 3.10: Read the traces, not just the metrics

**Problem.** Multi-agent systems are not debuggable from aggregate metrics alone. "First-pass rejection rate is 25%" tells you nothing about *why* the Evaluator is being soft, *what kind* of bugs the Generator misses, or *where* the Planner is over-specifying.

**Pattern.** The primary debugging surface is the run transcript. Every agent's every turn should be logged in a human-readable form. The harness developer's job is to sit with traces and find where each role's judgment diverged from the desired behavior, then tune that role's prompt.

This is the same muscle as reading a stack trace. There is no shortcut.

**Implementation.**

- Pipe every agent's output to `debug.log` with role + turn-number tags
- Have a second-tier agent (or human) grep through transcripts to find divergence patterns
- Use the divergence pattern to update the role's system prompt
- Iterate

**Anti-pattern.** "We'll just run more experiments and look at the aggregate metrics." Aggregate metrics tell you a system isn't working; traces tell you why.

---

## 4. SLAs and success metrics

| Metric | Target | Rationale |
|---|---|---|
| Run length without human intervention | > 4 hours | The whole point of long-running coordination |
| Adversarial-evaluator first-pass rejection rate | > 30% | Evaluator that rubber-stamps is not adversarial |
| Final-output rejection rate after negotiation completes | < 5% | Negotiated contracts should make rejections rare at end |
| Cross-role state transferred via file-system (vs context) | > 80% | File-system is the persistence layer |
| Compaction events without coherence drift | 100% | If compaction breaks the run, the harness is wrong |
| Contract criteria per artifact (granularity) | ≥ 20 | Vague criteria → vague critiques → no fix |
| Cost per successful long-run completion (tracked) | bounded; trended | Multi-agent is expensive; unit economics matter |
| Trace-readability score (subjective) | high | Engineers should be able to read what each role did |
| Time from new role addition to first successful run | < 1 day | Adding a role should be straightforward, not a refactor |

---

## 5. Build sequence

ACS is built in the following sequence from skeleton to first reference deployment. Each step depends on the previous one. Pace varies by team and tooling; the sequence does not.

| Step | Deliverable | Why |
|---|---|---|
| 1 | Three role prompts (Planner / Generator / Evaluator) · separate context windows · single shared filesystem workspace | Skeleton must enforce role separation from day one |
| 2 | Negotiated-contract protocol: markdown files on disk, Generator proposes, Evaluator counters, both agree before code | The contract is the load-bearing primitive |
| 3 | Adversarial-evaluator tuning: few-shot examples calibrating Evaluator harshness; tune until first-pass rejection rate > 30% | Evaluator that rubber-stamps is not adversarial |
| 4 | File-system artifact convention: feature-list.json, progress.md, contract.md, critique-log.md, debug.log, standardize names + shapes | Convention beats configuration; future runs are debuggable |
| 5 | Trace-reading workflow: every run produces a transcript; sit with traces and tune prompts before adding more roles | Primary debugging surface |
| 6 | Second domain (e.g. extend coding harness to research synthesis) | Proves the pattern transfers across artifact types |
| 7 | Optional: training-time coordination rewards (PARL-style) if you control post-training | Compounds the harness; doesn't replace it |
| 8 | Spec / one-pager / case study | Compounds future adoption |

---

## 6. Anti-patterns to avoid

| Anti-pattern | Why it breaks | What to do instead |
|---|---|---|
| Single agent that "manages itself" | Sycophancy collapse; same weights generate and evaluate | Role decomposition with separate context windows (principle #1) |
| Self-evaluation loop | Structurally biased to over-rate | Adversarial Evaluator agent (principle #2) |
| Up-front granular plan from a single Planner | Cascading errors over multi-hour runs | Vague plan + specialist-negotiated tactical detail (principles #3, #5) |
| Storing run-state in context window | Lost across compaction; coherence drift | File-system state (principle #4) |
| Full-mesh peer agents | O(n²) cost; coherence collapse past three agents | Orchestrator + specialists (principle #6) |
| Implicit handoffs via shared context | Lost across role boundaries | Explicit handoff primitive with passed state (principle #7) |
| Assuming outcome-RL produces coordination as emergent | Serial collapse | Coordination rewards during training (principle #8), or harness-side compensation |
| Static harness that doesn't evolve with the model | Token-cost overhead and unnecessary model constraint | Adaptive harness, retire scaffolding (principle #9) |
| Debugging from aggregate metrics only | Tells you what's broken, not why | Read the traces (principle #10) |

---

## 7. Compatibility with existing frameworks

ACS is framework-agnostic. The pattern can be implemented in any of these stacks:

- **Anthropic Claude SDK / Agent SDK:** sub-agents, skills, hooks, file-system tools all map directly
- **OpenAI Agents SDK:** handoffs (principle #7), tools, file-system tools all available natively
- **LangChain / LangGraph:** Supervisor pattern (principle #6), checkpoints, multi-graph composition
- **Microsoft AutoGen:** Magentic-One Orchestrator + specialist workers map directly
- **Letta (formerly MemGPT):** Shared memory blocks operationalize file-system state (principle #4)
- **Custom orchestration:** Three model API sessions + a shared `workspace/` directory is sufficient

ACS is also compatible with, and built on top of, these underlying standards:

- **Model Context Protocol (MCP):** Per-agent tool access in an ACS system goes through MCP servers
- **Progressive Discovery Spine (PDS):** When a single agent in an ACS system needs scoped tool discipline, PDS handles that layer
- **OpenTelemetry:** Trace logs (principle #10) emit OTel-compatible traces

---

## 8. References

### Foundational sources

- Anthropic, *Harness Design for Long-Running Application Development* ([anthropic.com](https://www.anthropic.com/engineering/harness-design-long-running-apps))
- Anthropic, *Effective Harnesses for Long-Running Agents* ([anthropic.com](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents))
- Anthropic, *How we built our multi-agent research system* ([anthropic.com](https://www.anthropic.com/engineering/multi-agent-research-system))
- Anthropic, *Building Effective Agents* ([anthropic.com](https://www.anthropic.com/research/building-effective-agents))
- Ash Prabaker & Andrew Wilson (Anthropic), *Build Agents That Run for Hours (Without Losing the Plot)*, AI Engineer Summit 2026 ([YouTube](https://www.youtube.com/watch?v=mR-WAvEPRwE))
- Moonshot AI, *Kimi K2.5 Tech Blog: Visual Agentic Intelligence* ([kimi.com](https://www.kimi.com/blog/kimi-k2-5))
- Microsoft Research, *Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks* (Fourney et al., 2024) ([arXiv:2411.04468](https://arxiv.org/abs/2411.04468))
- LangChain, *LangGraph Supervisor* ([github.com](https://github.com/langchain-ai/langgraph-supervisor-py))
- Cognition AI, *Multi-Agents: What's Actually Working* ([cognition.ai](https://cognition.ai/blog/multi-agents-working))
- OpenAI, *Agents SDK Handoffs* ([openai.github.io](https://openai.github.io/openai-agents-python/handoffs/))
- Letta, *Stateful Agents: Memory* ([docs.letta.com](https://docs.letta.com/guides/agents/memory/))
- Affaan Mustafa, *ECC (Everything Claude Code): Subagents documentation* ([github.com/affaan-m/ECC](https://github.com/affaan-m/ECC))

### Adjacent specifications

- Model Context Protocol: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- Progressive Discovery Spine: [github.com/drewmattie-code/Progressive-Discovery-Spine](https://github.com/drewmattie-code/Progressive-Discovery-Spine)

---

## 9. Versioning

This specification follows semantic versioning. Breaking changes to the conceptual model bump the major version; new principles or refinements bump the minor. Editorial fixes bump the patch.

- **v0.1-draft:** initial draft (2026-05-25). Internal review.
- **v1.0:** first public release under CC BY 4.0 + MIT (2026-05-28). Includes ECC convergence citation (Affaan Mustafa, *Everything Claude Code*).

---

## 10. Author

[Drew Mattie](https://www.linkedin.com/in/drew-mattie-88084826/) · SaaSquach AI Labs (a division of Charles & Roe Inc.) · 2026

ACS was developed at SaaSquach AI Labs (a division of Charles & Roe Inc.) as the architectural foundation for multi-agent AI products operating at production scale. It is the companion specification to the [Progressive Discovery Spine (PDS)](https://github.com/drewmattie-code/Progressive-Discovery-Spine). This specification is released as open documentation under [CC BY 4.0](LICENSE-CC-BY-4.0) so the pattern can be adopted, adapted, and built upon, with attribution.
