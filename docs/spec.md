# noesis — spec (draft)

Status: **brainstorm / spec only — no code yet.** Last updated 2026-11-08.
Open questions live in [open-questions.md](open-questions.md); source material in [references/](references/).

noesis is an **opinionated, keyboard-first TUI client of [herdr](https://herdr.dev)** for running AI coding
agents across several machines. It shows hosts, groups, agents and threads in a neo-tree-style sidebar, and
treats one centralized memory repo as the agent's long-term knowledge — the foundation for a "true personal
agent".

Scope of this document: the **tree view** and everything it depends on (data model, topology, transport, fork
and roll-up). The **main view** (conversation display when a node is opened) comes after the tree is done.

---

## 1. Principles

1. **TUI first, minimal mouse.** Every action has a key; nothing requires a click.
2. **One centralized memory.** All agents on all machines read and write the same knowledge repo
   (`person-claude-memory` on GitHub). This is noesis's first opinion.
3. **Machines run no noesis code.** A machine needs herdr, a way in (ET and/or SSH) and a checkout of the memory
   repo. All noesis logic lives on the hub.
4. **herdr owns live runtime, noesis owns structure.** herdr knows panes, agents and their status; noesis owns
   groups, ordering, folds and thread lineage.

## 2. Vocabulary

| Term | Meaning | herdr equivalent |
|---|---|---|
| **hub** | The host where the noesis TUI runs. Owns the layout. Also a machine for its own agents. | the local herdr client |
| **machine** | Any host running a herdr server + agents that the hub connects to. | herdr server (one session) |
| **group** | Generic, nestable container for agents. A "project" is just a group. Belongs to exactly one machine. | none — noesis-owned |
| **agent** | A live agent process running in a herdr pane (claude, codex, …). | agent in a pane |
| **thread** | An agent's conversation. Can be resumed after the process exits and can fork. | `AgentSessionInfo` (`agent_session_id`, `agent_session_path`, `resume_argv`) |

"Session" is deliberately **not** used: herdr already uses it for its persistent server session.
One agent may run several threads over its lifetime; a thread can outlive its agent.

## 3. Tree view

### 3.1 Shape

Hosts are **not** a tree level. Root nodes are groups, labelled with their machine:

```
▾ ⚠ @cws hiennhahien
  ▾ ● ordering
    ● claude  push-alerts          working
    ▾ ⚠ claude  checkout-flow      needs input
      └─⑂ why-vnd-rounding         idle      ← forked thread
  ▸ ● ops                          (2 ●)
▸ ● @pi photo-frame
▸ ○ @cws (ungrouped)
▸ ✕ @mac dotfiles                  offline
```

Hierarchy: `root group (@machine) → subgroup* → agent → thread*` (threads nest when forks are forked).

### 3.2 Rules

- **Root label:** `{status} @<machine> <group>`. Subgroups inherit the machine and don't repeat it.
- **Groups nest arbitrarily** and are **not tied to a cwd or repo** — one group may span several repos.
- **A group belongs to exactly one machine.** No cross-machine groups; a multi-machine project is two roots.
- **Every machine has an `@<machine> (ungrouped)` root** where unfiled agents land.
- **Status rolls up recursively:** a collapsed node shows the most urgent state beneath it plus counts
  (`▸ ● ops (2 ●)`, `▸ ⚠ clients (1 ⚠)`).
- **Offline machines keep their tree**, rendered from the last-known state and marked `✕ offline`; commands to
  them are disabled until they reconnect.
- **Ordering is manual** for root groups (machines may interleave), subgroups, agents and threads.
- **Moves never cross machines.** Pasting/indenting a node under another machine's root is refused.
- **Subgroups copy their parent's context when created** — a snapshot, not live inheritance (see §6.3).

### 3.3 Status glyphs (draft)

| Glyph | Meaning |
|---|---|
| `⚠` | needs input / blocked |
| `●` | working |
| `○` | idle / done |
| `⑂` | forked thread |
| `✓` | thread rolled up into knowledge |
| `✕` | machine offline |
| `!` | attention: `! auth`, `! rollup`, `! error` |

### 3.4 Keymap (draft — see open questions)

| Key | Action |
|---|---|
| `j` / `k` | move cursor |
| `h` / `l` | fold / unfold |
| `Enter` | focus the agent (opens main view, later) |
| `J` / `K` | move node down / up among its siblings |
| `>` / `<` | indent / outdent (re-parent under the previous sibling / up one level) |
| `x` then `p` | cut and paste a node (with its subtree) |
| `a` | new agent in the group under the cursor |
| `A` | new subgroup under the cursor |
| `r` | rename |
| `d` | close / delete (with confirmation) |
| `f` | fork the thread under the cursor |
| `u` | roll up the thread under the cursor |
| `R` | re-authenticate the machine (opens its SSH login in a herdr pane) |
| `/` | filter |
| `]a` / `[a` | jump to next / previous agent that needs input |

`]a` (attention navigation) is the feature that should make noesis better than herdr's own sidebar.

## 4. Topology

```
┌─────────────────────────── HUB (where the TUI lives) ───────────────────────────┐
│                                                                                 │
│  ┌─────────────── noesis ───────────────┐      ┌───── herdr (local) ─────┐      │
│  │ TUI: tree view (main view later)     │      │ server + herdr.sock     │      │
│  │ core: machine registry, tree model   │─────>│ hub's own agents        │      │
│  │ transports: et, ssh fallback         │ unix │ (hub is a machine too)  │      │
│  │ layout store (local file):           │      └─────────────────────────┘      │
│  │   groups, order, folds, lineage      │                                       │
│  └───────┬──────────────────┬───────────┘      et client, OpenSSH client        │
│          │                  │                  memory checkout                  │
└──────────┼──────────────────┼───────────────────────────────────────────────────┘
           │                  │
           │ ET :2022         │ SSH :22 (fallback; re-auth)
           │ (survives sleep) ├─────────────────────────────┐
           │                  │                             │ SSH :22
           v                  v                             v
┌───────────── MACHINE: cws ─────────────┐   ┌──────── MACHINE: pi ────────┐
│ etserver -> socat 127.0.0.1:N ──┐      │   │ sshd -> unix-socket fwd ──┐ │
│ sshd -> unix-socket fwd ────────┤      │   │                           │ │
│                                 v      │   │                           v │
│ herdr server + herdr.sock              │   │ herdr server + herdr.sock   │
│   workspaces, tabs, panes              │   │   agents, threads           │
│   agents (claude, ...), threads        │   │   transcripts               │
│   transcripts (~/.claude/.../*.jsonl)  │   │                             │
│ memory checkout                        │   │ memory checkout             │
└───────────────────┬────────────────────┘   └──────────────┬──────────────┘
                    │ git pull / push                       │ git pull / push
                    v                                       v
┌──────────────────────── GitHub: person-claude-memory ────────────────────────┐
│ memories (one file each), index, groups/<machine>/<group>.md contexts        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Where things live

| Location | Components |
|---|---|
| **Hub only** | noesis TUI + core, layout store, transports, machine registry (with transport preference per machine) |
| **Every machine** | herdr server, agents and their transcripts, memory repo checkout |
| **ET machines (cws)** | `etserver` and a socat bridge from `127.0.0.1:<port>` to `herdr.sock` |
| **GitHub** | memories, memory index, group contexts — the only state shared between hosts |

### 4.2 Flows

| Flow | Path | Content |
|---|---|---|
| Status | machine herdr → transport → hub | `events.subscribe` stream; on (re)connect: subscribe, then `session.snapshot` |
| Commands | hub → transport → machine herdr | `agent.start`, `agent.prompt`, `agent.wait`, `pane.close`, … |
| Memory | each machine ↔ GitHub | agents pull before start; child agents push on roll-up |
| Setup (once, manual) | you | `herdr --remote <host>` to install/start herdr; install `etserver`; run the socat bridge as a user service |

## 5. Transport

noesis talks herdr's **JSON socket API directly** (newline-delimited JSON over the machine's `herdr.sock`)
instead of using herdr's `--machine` CLI forwarding. Reasons:

- `--machine` is **SSH-only** (OpenSSH + ControlMaster), so it can't use ET.
- `--machine` is request/response only — `events.subscribe` isn't among the forwarded commands — so the hub
  would have to poll. A direct socket stream gives live events.

### 5.1 Model

```
noesis core ──herdr JSON API──> Transport ──> remote herdr.sock
                                ├─ et  : ET port forward → socat on remote → herdr.sock
                                └─ ssh : OpenSSH unix-socket forward (-L local.sock:remote.sock)
```

- A transport only provides **byte streams to the remote herdr socket**. It must support **several
  concurrent connections** — herdr wants one long-lived connection per subscription plus separate connections
  for requests and snapshots.
- **Per machine:** an ordered transport list, e.g. `cws: [et, ssh]`, `pi: [ssh]`. **Automatic fallback** to the
  next transport when one can't connect. (Decided 2026-11-08.)
- **ET is primary on the workspace cws** (ET is allowed there). ET logs in via SSH once, then survives hub
  sleep and network changes without a new SSH login — this addresses the daily re-auth + sleep problem.
- **Reconnect** is the transport's job. After reconnecting, follow herdr's recovery protocol: open a new
  subscription, wait for `subscription_started`, then `session.snapshot` on another connection; treat events
  as invalidation signals, never replay them onto the snapshot. Same on `events_lost`.
- **Re-auth is visible, never prompted by noesis.** When SSH needs a login, the root shows `! auth`; `R` opens
  the machine's login in a herdr pane.
- **Version check on connect:** read protocol metadata (`ping` / `session.snapshot`) and refuse protocol
  versions noesis doesn't know. Ignore unknown fields (herdr's stated compatibility rule).

### 5.2 Trade-offs accepted

- noesis does not use `herdr machine add` / `--machine`. herdr's own UI may keep its SSH machines alongside.
  Remote install/setup stays manual via `herdr --remote <host>`.
- The ET path's socat bridge exposes the herdr socket on remote `127.0.0.1` — reachable by **any local user
  on that machine**. Fine on a single-user VM; a risk on a shared host. (Direct unix-socket forwarding over ET
  would avoid it — unverified, see open questions.)
- noesis depends on herdr's socket protocol (protocol 22 at herdr 0.9.5) rather than its CLI.
- The hub can drive agents on every machine, so its SSH/ET credentials are the most sensitive thing in the setup.

### 5.3 Identity

herdr ids (`w1:p1`, agent names) are scoped to one server and may change across herdr restarts. noesis keys:

- agents and panes by `(machine, herdr id)` for live operations;
- **threads by `(machine, agent_session_id)`** for anything persisted (layout, lineage). Session ids survive
  restarts, and `resume_argv` lets noesis bring a dead thread back.

## 6. Threads and knowledge

### 6.1 Purpose (v0.1)

Threads are for **non-code work**: planning, investigation, collecting insights. Their output is knowledge in
the central memory repo, not code. (Code-producing forks with worktrees are out of scope for v0.1.)

### 6.2 Fork (`f`)

- Creates a **new pane in the same cwd** with a forked conversation (e.g. `claude --resume <id> --fork-session`).
- Forks start with **normal permissions** — no forced plan/read-only mode for now (relaxed 2026-11-08).
- The new thread appears as a child of the source thread (`⑂`); lineage (`parent_thread`) is stored by noesis.
- Forks may be forked again.

### 6.3 Group context

- Group knowledge is **a view into the central memory**, not a separate store: each group has a context file in
  the memory repo, `groups/<machine>/<group-id>.md`, which points at relevant memories and holds group-specific
  notes.
- **Subgroups copy the parent's context file when created** and then evolve independently. Because the file
  holds pointers, shared memories are not duplicated.
- How agents *load* group context at start is open (see open questions).

### 6.4 Roll-up (`u`)

The **child agent writes and pushes its own memory file**; noesis only orchestrates. (Decided 2026-11-08.)

```
hub (noesis)                         machine (child agent)                 GitHub
─────────────                        ─────────────────────                 ──────
1. agent.prompt(child, ROLLUP) ───>  2. distill findings
                                     3. write memory/<date>-<slug>.md
                                     4. append index line
                                     5. pull --rebase, commit, push ──────> repo
6. agent.wait(child, idle|done) <──  (prints ROLLUP-DONE <commit-sha>)
7. verify: sha exists on GitHub
8. agent.prompt(parent, "learned X, see <file>")
9. close child pane; node -> "✓ <slug> -> knowledge"
```

What noesis owns:

- **The roll-up prompt template** — the only thing keeping memory consistent: filename pattern, frontmatter
  (`name`, `description`, `type`, `group:`, `machine:` tags), index line format, "never edit other memory
  files", "retry push on rejection".
- **A machine-readable finish line:** the child ends with `ROLLUP-DONE <sha>` or `ROLLUP-FAILED <reason>`,
  read via `agent.read`.
- **Verify before closing:** the child pane closes only after the commit is visible on GitHub. On failure the
  thread stays open and shows `! rollup`.
- **Concurrent writers are expected** (every machine writes). Safety comes from one new file per memory, an
  append-only index (conflicts resolve by keeping both lines), and pull-rebase-retry.
- Nested forks roll up to their **direct parent thread**; knowledge always goes to the memory repo.

## 7. State

| State | Owner | Where |
|---|---|---|
| Panes, agents, status, transcripts | herdr | each machine |
| Groups, order, folds, thread lineage, machine registry | noesis | hub, local file (format open) |
| Memories, index, group contexts | everyone | GitHub `person-claude-memory` |

Layout stays on the hub (not synced) because there is one hub and layout changes constantly.

## 8. Decision log

| Date | Decision |
|---|---|
| 2026-11-07 | "thread" replaces "session" for an agent conversation |
| 2026-11-07 | groups are generic and nestable; a project is a group; not tied to cwd/repo |
| 2026-11-07 | a group belongs to one machine; roots are labelled `{status} @<machine> <group>` |
| 2026-11-07 | v0.1 threads are non-code; fork = conversation fork; roll-up = knowledge |
| 2026-11-07 | centralized memory = `person-claude-memory` (opinion #1) |
| 2026-11-07 | subgroups copy parent context at creation |
| 2026-11-08 | forks are not locked to read-only (for now) |
| 2026-11-08 | hub/machine topology; layout lives on the hub |
| 2026-11-08 | every machine writes to the memory repo directly |
| 2026-11-08 | noesis owns transport: ET primary (allowed on workspace cws), automatic SSH fallback |
| 2026-11-08 | roll-up: child agent writes + pushes its own memory file |
