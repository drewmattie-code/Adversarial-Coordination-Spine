# ACS Claude skills

This directory holds the ACS architectural-consultant skill in a format that drops directly into Claude Code, Codex, Cursor, and other clients that support the skills convention.

## Install for Claude Code

```bash
mkdir -p ~/.claude/skills/acs
cp acs/SKILL.md ~/.claude/skills/acs/SKILL.md
```

Restart your Claude Code session (or run `/help` and confirm the skill appears).

The skill will then activate automatically when you ask architectural questions about multi-agent coordination, long-running agent harnesses, evaluator agent design, or any of the other triggering contexts described in the SKILL frontmatter.

## What the skill does

It's an architectural consultant, not a code library. When triggered, Claude (or another supporting agent) will:

1. Diagnose which of the four documented multi-agent failure modes you're hitting (sycophancy collapse, cascading planning errors, serial collapse, coherence drift)
2. Recommend the 2-3 ACS principles that address it
3. Give one concrete next step
4. Link to the full spec for deeper reading

It will NOT install software, pretend to be a runnable library, or recite the whole spec at you. The point is fast diagnosis.

## Composition with PDS

If the user is also building agents against enterprise data, the [PDS skill](https://github.com/drewmattie-code/Progressive-Discovery-Spine) applies in parallel. ACS coordinates many agents; PDS scopes the tool surface of one agent. Install both when both apply.

```bash
mkdir -p ~/.claude/skills/acs ~/.claude/skills/pds
curl -fsSL https://raw.githubusercontent.com/drewmattie-code/Adversarial-Coordination-Spine/main/dist/skills/acs/SKILL.md \
  -o ~/.claude/skills/acs/SKILL.md
curl -fsSL https://raw.githubusercontent.com/drewmattie-code/Progressive-Discovery-Spine/main/dist/skills/pds/SKILL.md \
  -o ~/.claude/skills/pds/SKILL.md
```

## Other clients

The SKILL.md format is portable. Drop it into:

- **Cursor:** `~/.cursor/skills/acs/SKILL.md`
- **Codex:** `~/.codex/skills/acs/SKILL.md`
- Any other agent that supports the SKILL.md / agent-skill convention

For agents that don't natively support the skills convention, the SKILL.md is also readable as a prompt. Paste it into a system prompt or context.

## Versioning

The skill version tracks the spec version. Current: v0.1-draft (matches SPEC.md v0.1-draft).

When the spec evolves, the skill evolves with it. Watch this repo for updates.

## Attribution

Adversarial Coordination Spine by Drew Mattie · SaaSquach AI Labs (a division of Charles & Roe Inc.) · CC BY 4.0
