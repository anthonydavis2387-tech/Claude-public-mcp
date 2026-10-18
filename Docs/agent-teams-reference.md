# Agent Teams: Master Reference Guide

A working reference for designing, running, and improving Claude Code **agent
teams** in this project. It is written for Claude (and humans) to consult before
spawning teammates or writing new agent definitions.

> Source: official Claude Code docs (`code.claude.com/docs/en/agent-teams`,
> `/sub-agents`, `/costs`), checked 2026-10-18. Agent teams are
> **experimental**; behavior and version-gated details change quickly. When a
> detail here matters, re-check the live docs.

---

## 1. What an agent team is

An agent team is several Claude Code sessions working together:

| Component     | Role |
| :------------ | :--- |
| **Team lead** | The main session. Spawns teammates, creates tasks, coordinates, synthesizes results. Fixed for the session's lifetime. |
| **Teammates** | Separate, full Claude Code instances. Each has its **own context window** and works independently. |
| **Task list** | Shared work items (pending → in progress → completed), with dependencies. Teammates claim work from it. |
| **Mailbox**   | Messaging between agents. Any agent can message any other **by name**. |

Teammates talk to each other directly. The user can also talk to any teammate
without going through the lead.

### Teams vs. subagents vs. other options

| | Subagents | Agent teams |
| :- | :- | :- |
| Context | Own window; result returns to caller | Own window; fully independent |
| Communication | Return a result (named subagents can be messaged) | Teammates message each other directly |
| Coordination | Main agent manages everything | Self-coordination + shared task list |
| Best for | Focused tasks where only the result matters | Work that needs discussion, challenge, collaboration |
| Token cost | Lower (summary returns) | Higher (each teammate is a full instance) |

**Lighter alternatives to try first:**
- **Subagents**: quick, focused workers that report back.
- **Cross-session messaging**: pass findings between sessions you run yourself.
- **Git worktrees**: run parallel sessions manually, with no automated coordination.

---

## 2. When to use a team (decision guide)

Use a team when **parallel, independent exploration adds real value**:

- **Research and review**: several angles at once, then share and challenge findings.
- **New modules or features**: each teammate owns a separate piece.
- **Debugging with competing hypotheses**: teammates test rival theories and try to disprove each other.
- **Cross-layer work**: frontend / backend / tests, each owned by a different teammate.

**Do not** use a team for:
- Sequential tasks where step N depends on step N-1.
- Edits to the same file(s). Two teammates editing one file leads to overwrites.
- Work with many dependencies between pieces.
- Routine, small tasks. A single session is cheaper and faster.

Quick test before spawning:
1. Can the work split into pieces that **don't wait on each other**? If not, don't use a team.
2. Does each piece have a **clear deliverable** (a function, a test file, a review)? If not, refine the plan first.
3. Can each teammate **own distinct files**? If not, re-split or use one session.
4. Is the benefit worth **several times the tokens**? If not, use subagents.

---

## 3. Enabling and environment

Teams are off by default. This project enables them in
`.claude/settings.local.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Important side effects and constraints:
- **Named subagents become teammates.** While teams are enabled, any Agent tool
  call with a `name` launches a teammate, except a fork or a call that passes
  `isolation`. Claude Code doesn't ask for confirmation, so teams can form when
  nobody asked for one. Set the variable to `"0"` to revert. The change applies
  to the running session on save.
- **Interactive only.** In non-interactive mode (`-p`, Agent SDK), no teammates
  are spawned; named subagents run as ordinary subagents.
- **Settings precedence:** project, local, `--settings`, and managed settings
  override user settings, so any of them can switch teams back on.

### Display modes (`teammateMode`)

| Value | Behavior |
| :- | :- |
| `"in-process"` (default) | All teammates in the main terminal. Works anywhere. |
| `"auto"` | Split panes if already inside tmux, or iTerm2 with the `it2` CLI; else in-process. |
| `"tmux"` | Split panes; auto-detects tmux vs. iTerm2. |
| `"iterm2"` | iTerm2 native panes; requires the `it2` CLI and the iTerm2 Python API enabled. |

Set it in `~/.claude/settings.json` (`"teammateMode": "auto"`) or per session with
`claude --teammate-mode auto`. Split panes don't work in the VS Code integrated
terminal, Windows Terminal, or Ghostty.

### In-process controls
- **Up/Down**: select a teammate in the agent panel. **Enter** opens its transcript so you can message it.
- **Escape**: clear the selection, or interrupt the teammate you're viewing.
- **`x`**: stop the selected teammate. **Ctrl+T**: toggle the task list.
- While you're viewing a teammate, plain text and skills go to that teammate. `/compact`, `/clear`, and `/rewind` act on the lead and ask for confirmation. `/model` and `/fast` are blocked there, because a teammate's model is fixed when it spawns.
- Idle rows hide 30s after the whole panel goes idle; more than 3 idle teammates collapse into an `N idle agents` row. A hidden teammate is still running and addressable.

---

## 4. Architecture and storage

- **Team name:** `session-` + first 8 chars of the session ID. **One team per session.**
- **Team config:** `~/.claude/teams/{team-name}/config.json`, holding runtime state
  (session IDs, pane IDs, a `members` array). The lead's type is `team-lead`.
  **Never hand-edit or pre-author it**, because it gets overwritten. It is deleted when the session ends.
- **Mailboxes:** `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`. A message
  counts as sent only when the write succeeds. Malformed entries are dropped.
- **Task list:** `~/.claude/tasks/{team-name}/`. Persists after the session (see `cleanupPeriodDays`).
- **No project-level team config exists.** A file like `.claude/teams/teams.json`
  is just a file. Reusable roles go in **subagent definitions** (section 7).
- Task claiming uses file locking. Completing a task auto-unblocks its dependents.

### What a teammate knows at spawn
- **Loads:** CLAUDE.md, MCP servers, skills (same sources as a normal session;
  respects the lead's `--setting-sources`).
- **Receives:** the lead's **spawn prompt**.
- **Does NOT receive:** the lead's conversation history. So **everything
  task-specific must be in the spawn prompt.**

### How information flows
- Messages are delivered automatically; nobody needs to poll.
- When a teammate finishes, it sends the lead an **idle notification containing
  its final answer**. If its turn ended on an API error, it reports the failure and the error text.
- Messaging is one-to-one by name. To reach everyone, send one message per recipient.
- Agents without the Task tools coordinate through messages only.

---

## 5. Spawning a team well

### Model selection order (first match wins)
1. The model named in the spawn prompt for that teammate.
2. The subagent definition's `model` (`inherit` means the lead's model).
3. `CLAUDE_CODE_SUBAGENT_MODEL` (if not `inherit`).
4. The lead's current model.

`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` skips 1 and 2. The org `availableModels`
allowlist can substitute a model. Teammates inherit the lead's effort level.
(`teammateDefaultModel` was removed; name the model in the prompt instead.)

### Sizing
- **Team size:** start with **3–5 teammates**. Cost scales roughly linearly, coordination
  overhead grows, and returns diminish. Three focused teammates often beat five scattered ones.
- **Tasks:** aim for **5–6 tasks per teammate**, so the lead can rebalance. With 15 independent tasks, 3 teammates is a good start.
- **Task granularity:** a task too small costs more to coordinate than it saves. A task too large runs without check-ins and risks wasted work. The right size is a self-contained unit with a clear deliverable.

### Naming
Tell the lead what to call each teammate (e.g. `security`, `perf`, `tests`).
Predictable names make later instructions ("ask security to…") reliable.

### Anatomy of a strong spawn prompt
Every spawn prompt should include:
1. **Role / lens**: what this teammate is responsible for, and what it is *not*.
2. **Scope**: exact paths or modules it owns (and files it must not touch).
3. **Context**: facts the lead knows that aren't in CLAUDE.md (stack, constraints, decisions so far).
4. **Deliverable**: concrete output and format (e.g. "findings with severity ratings", "a passing test file at …").
5. **Done criteria**: how it knows it's finished, and what to verify.
6. **Collaboration rules**: who to message about what, and when to challenge others.

Keep it focused: everything in the spawn prompt is in the teammate's context from turn one.

### Plan-before-implement
Put the **lead in plan mode** before spawning, and teammates start in read-only
plan mode. When a teammate's plan is ready it sends a plan approval request. **The
lead's session auto-approves it without review**, so plan mode is a pacing tool, not a
safety gate. Edits and commands afterward still go through normal permission prompts.

---

## 6. Prompt templates

**Parallel review**
```text
Spawn three teammates to review PR #142, named security, perf, and tests:
- security: auth, injection, secrets handling
- perf: hot paths, N+1 queries, allocations
- tests: coverage gaps and missing edge cases
Each reports findings with severity and file:line. Don't overlap lenses.
Wait for all three, then synthesize one prioritized list.
```

**Competing hypotheses (debugging)**
```text
Users report <symptom>. Spawn 4 teammates, each owning one hypothesis:
<H1>, <H2>, <H3>, <H4>. Each must gather evidence for its own theory AND
message the others to try to disprove theirs, like a scientific debate.
Record the surviving explanation and its evidence in docs/findings.md.
```

**Feature build with file ownership**
```text
Implement <feature>. Spawn 3 Sonnet teammates:
- api: owns src/api/** only
- ui: owns src/ui/** only
- tests: owns tests/** only; writes tests against the agreed interface below
Interface contract: <types/endpoints>. Do not edit files outside your area;
message the owner instead. Create tasks with dependencies so tests waits on api.
```

**Design exploration**
```text
Spawn three teammates to explore <design question>: one on UX, one on
technical architecture, one playing devil's advocate against both.
```

**Useful steering lines**
- `Wait for your teammates to complete their tasks before proceeding.` (Use when the lead starts doing the work itself.)
- `Split the work into smaller tasks, about 5 per teammate.`
- `Ask the <name> teammate to shut down.`
- `Keep going: tasks <x, y> are not actually complete.` (Use when the lead stops early.)

---

## 7. Reusable roles: subagent definitions as teammates

Define a role once in `.claude/agents/<name>.md` (project, committed) or
`~/.claude/agents/` (user), then spawn it as a teammate with:
`Spawn a teammate using the security-reviewer agent type to audit src/auth/.`

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities. Use for auth, input handling, secrets, and dependency risk.
tools: Read, Grep, Glob, Bash
model: sonnet
---

You are a security reviewer. For each finding give: severity
(critical/high/medium/low), file:line, the concrete exploit path, and a
minimal fix. Do not edit files. Report only issues you can trace to a real
input or caller; label anything speculative as such.
```

How each field applies **to a teammate**:

| Field | Applied to teammate? |
| :- | :- |
| `tools` | Yes. The teammate is limited to the list; in-process teammates also always get `SendMessage` and the Task tools. |
| `model` | Yes, unless the spawn prompt names a model. |
| `disallowedTools` | In-process only. It can't remove `SendMessage` or the Task tools. |
| `effort`, `autoCompactWindow` | In-process only. |
| Body (system prompt) | In-process: **appended** to the default prompt. Split-pane: **replaces** it. |
| `skills` | **Not applied.** Teammates load skills from project/user settings. |
| `mcpServers` | Split-pane only. In-process teammates use project/user MCP config. |

Other frontmatter (for subagent use generally): `name` and `description`
(required), `permissionMode`, `hooks`, `memory` (`user`/`project`/`local`),
`background`, `isolation: worktree`, `color`, `omitClaudeMd`, `initialPrompt`.
Unknown fields are silently ignored, and names are camelCase.

**Writing descriptions:** say specifically *when* to use the agent. Keep it
short, and put detailed instructions in the body, which loads only when the agent runs.
Avoid `background: true` on roles meant for teammates, because in-process teammates
can't run background subagents.

**Trust:** after a restart, a definition from `.claude/agents/` is re-applied to a
revived teammate only if that exact folder is trusted.

---

## 8. Permissions and safety

- Teammates start with the **lead's permission mode** (except `dontAsk`, which isn't
  inherited). If the lead runs with `--dangerously-skip-permissions`, so do all teammates.
- Per-teammate modes can be changed **after** spawn, not at spawn.
- **Teammate permission prompts surface in the lead session.** Pre-approve common
  safe operations in permission settings before spawning to cut interruptions.
- A message from another agent is marked as coming from a Claude session, not the
  user. A teammate **cannot** grant consent on the user's behalf or relay a denied
  action to another teammate to get around a check. In auto mode, the classifier
  treats relayed approvals as untrusted and may block messages between agents.

---

## 9. Quality gates with hooks

Configure in settings under `hooks`. Exit code **2** blocks the action and sends
stderr back as feedback.

| Hook | Fires when | Exit 2 does |
| :- | :- | :- |
| `TeammateIdle` | A teammate is about to go idle | Sends feedback and keeps it working |
| `TaskCreated` | A task is being created | Prevents creation, sends feedback |
| `TaskCompleted` | A task is being marked complete | Prevents completion, sends feedback |

Typical uses: refuse `TaskCompleted` until tests/lint pass; keep a teammate going
on `TeammateIdle` if its deliverable file is missing; reject vague `TaskCreated`
titles. Keep hook scripts fast, because they run on every event.

---

## 10. Cost management

- Teams use **far more tokens** than one session (about **7x** when teammates run in plan mode).
- **Use Sonnet for teammates** unless a role truly needs a stronger model.
- **Keep teams small** and **spawn prompts focused**.
- **Shut teammates down** when they're done. Idle-but-alive teammates still cost tokens.
- In-process teammate prompt cache lasts 5 min by default; set
  `subagentPromptCacheTtl: "1h"` for long-running teams (1h cache writes cost more).
- Check `/usage` for the subagent/teammate share.

---

## 11. Monitoring, troubleshooting, limitations

**Steer actively.** Check progress, redirect approaches that aren't working, and
synthesize findings as they come in. Unattended teams waste effort.

| Symptom | Fix |
| :- | :- |
| Teammates don't appear | Check the agent panel (arrows + Enter). The task may be too simple; explicitly ask for "an agent team". For split panes: `which tmux` / check `it2`. |
| Got subagents instead of a team | Ask again and explicitly request an agent team. |
| Got teammates when you wanted subagents | Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to `"0"`. |
| Too many permission prompts | Pre-approve common operations before spawning. |
| A teammate stopped on an error | Open it and give instructions, or spawn a replacement. |
| Lead declares done too early | Tell it to keep going and name the incomplete tasks. |
| Lead does the work itself | "Wait for your teammates to complete their tasks before proceeding." |
| Task stuck as in progress | Verify the work is done, then update the status or have the lead nudge the teammate. |
| Orphaned tmux session | `tmux ls`, then `tmux kill-session -t <name>`. |

**Known limitations**
- `/resume` and `/rewind` don't restore in-process teammates. Spawn new ones after resuming.
- Task status can lag and block dependents.
- Shutdown is slow: teammates finish their current call first.
- One team per session, no nesting (teammates can't spawn teammates), and the lead can't be transferred.
- In-process teammates can't run background subagents.

---

## 12. Pre-flight checklist

Before spawning:
- [ ] The work splits into independent pieces with clear deliverables.
- [ ] Each teammate owns distinct files; shared interfaces are written down.
- [ ] 3–5 teammates, ~5–6 tasks each, with names chosen.
- [ ] Each spawn prompt has role, scope, context, deliverable, done criteria, and collaboration rules.
- [ ] Models chosen (Sonnet by default) and permissions pre-approved.
- [ ] Quality-gate hooks are in place if correctness matters.

After the run:
- [ ] All tasks are actually complete and verified, not just marked.
- [ ] Findings are synthesized by the lead into one result.
- [ ] Teammates are shut down.
- [ ] Lessons are recorded in section 13.

---

## 13. Lessons learned (project log)

Add an entry after each meaningful team run, recording what worked, what didn't,
and what to change in prompts or agent definitions next time.

| Date | Task | Team shape | What worked | What to change |
| :- | :- | :- | :- | :- |
| | | | | |
