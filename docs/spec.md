# noesis — spec (draft)

Status: **brainstorm / spec only — no code yet.** Last updated 2026-11-08.
Open questions live in [open-questions.md](open-questions.md); source material in [references/](references/).

noesis is an **opinionated, keyboard-first TUI built on top of
[herdr-core](https://github.com/herdrdev/herdr-core)** (`hc`) for running AI coding agents across several
machines. herdr-core is a terminal runtime that "draws nothing": it runs programs in terminals that outlive
their viewer, connects machines, and exposes everything over a JSON-RPC API. noesis is the opinionated layer
on top: a neo-tree-style view of groups, agents and threads, plus one centralized memory repo as the agent's
long-term knowledge — the foundation for a "true personal agent".

noesis is **not** a client of the herdr app (the older workspace/tab/pane UI). It talks only to herdr-core.

Scope of this document: the **tree view** and everything it depends on (data model, topology, connections,
fork and roll-up). The **main view** (conversation display when a node is opened) comes after the tree is done.

---

## 1. Principles

1. **TUI first, minimal mouse.** Every action has a key; nothing requires a click.
2. **One centralized memory.** All agents on all machines read and write the same knowledge repo
   (`person-claude-memory` on GitHub). This is noesis's first opinion.
3. **Machines run no noesis code.** A machine needs `hc`, a way in (ET and/or SSH) and a checkout of the memory
   repo. All noesis logic lives on the hub.
4. **herdr-core owns runtime, noesis owns meaning.** hc knows terminals, their status, parents, labels and
   machines; noesis decides what a group, an agent and a thread are, and keeps order, folds and roll-up state.

## 2. Vocabulary

| Term | Meaning | herdr-core equivalent |
|---|---|---|
| **hub** | The host where the noesis TUI runs, next to the local hc core. Owns the layout. Also a machine for its own agents. | the local core |
| **machine** | Any host whose hc core the hub's core has added. | `hc machine add` (name like `cws`) |
| **group** | Generic, nestable container for agents. A "project" is just a group. Belongs to exactly one machine. | none — noesis-owned (possibly stored as labels/docs, open) |
| **agent** | A live agent program (claude, codex, …) running in an hc terminal. | terminal (`cws/t3`) |
| **thread** | An agent's conversation. Can be resumed after the program exits and can fork. | none — hc has no conversation concept; noesis records it (open) |

"Session" is deliberately **not** used: hc uses it for separate core sessions on one host
(`--session scratch`). One agent may run several threads over its lifetime; a thread can outlive its agent.

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

Status comes from hc, which stores whatever the program reports through **OSC 7501** (`idle`, `working`,
`done`, `blocked`, `error`, …). hc never guesses from screen text, so an agent that doesn't report has no
status (open question: making Claude report).

| Glyph | Meaning |
|---|---|
| `⚠` | `blocked` (needs input) or `error` |
| `●` | `working` |
| `○` | `idle` / `done` |
| `·` | no status reported |
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
| `R` | re-authenticate the machine (runs `hc machine login <machine>` in a terminal) |
| `/` | filter |
| `]a` / `[a` | jump to next / previous agent that needs input |

`]a` (attention navigation) is the feature that should make noesis better than a flat terminal list.

## 4. Topology

```
┌─────────────────────────── HUB (where the TUI lives) ───────────────────────────┐
│                                                                                 │
│  ┌─────────────── noesis ───────────────┐      ┌──── hc core (local) ────┐      │
│  │ TUI: tree view (main view later)     │      │ machine connections     │      │
│  │ tree model, layout, roll-up          │─────>│ one terminal list and   │      │
│  │ via helper: et, then ssh             │ JSON │ event stream for all    │      │
│  │                                      │ -RPC │ docs (layout store?)    │      │
│  └──────────────────────────────────────┘      │ hub's own terminals     │      │
│                                                └──┬───────────────┬──────┘      │
│  memory checkout                                  │               │             │
└───────────────────────────────────────────────────┼───────────────┼─────────────┘
                                                    │               │
                    ┌───────────────────────────────┘               │
                    │ ET (survives sleep)                           │ SSH
                    │ via --via helper                              │ hc machine add
                    v                                               v
┌───────────── MACHINE: cws ─────────────┐   ┌──────── MACHINE: pi ────────┐
│ etserver -> bridge -> hc connect       │   │ sshd -> hc connect          │
│ (ssh -> hc connect as fallback)        │   │                             │
│                                        │   │                             │
│ hc core (remote)                       │   │ hc core (remote)            │
│   terminals: agents, threads           │   │   terminals: agents         │
│   status via OSC 7501, labels          │   │   status, labels            │
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
| **Hub only** | noesis TUI, the local hc core (holds every machine connection), the via helper script, layout |
| **Every machine** | hc core, agent terminals and their transcripts, memory repo checkout |
| **ET machines (cws)** | `etserver` and a bridge that runs `hc connect` for incoming ET connections |
| **GitHub** | memories, memory index, group contexts — the only state shared between hosts |

### 4.2 Flows

| Flow | Path | Content |
|---|---|---|
| Status | remote core → local core → noesis | one `events.subscribe` stream covering all machines (`cws/t7`) |
| Commands | noesis → local core → remote core | `terminal.run` / `send` / `wait` / `read` / `kill` with `on: <machine>` or full addresses |
| Memory | each machine ↔ GitHub | agents pull before start; child agents push on roll-up |
| Setup (once, manual) | you | install `hc` and add machines (`hc machine add`, with `--via` for ET); install `etserver` and the bridge on cws |

## 5. Connections

### 5.1 noesis ↔ local core

- noesis opens the **local hc core's unix socket** and speaks JSON-RPC 2.0, one message per line (plain mode).
  It never connects to remote machines itself: the local core already keeps every machine connection and
  **combines all terminals and events into one list and one stream**, addressed as `cws/t7`.
- Framed mode (`hello {framed: true}`) is only needed for `terminal.attach` streams — i.e. the main view later.
- **Event handling** (from the hc API docs): `events.subscribe` replies with a snapshot and `seq`; apply
  events in `seq` order using the per-type rules (`created`, `status`, `labels`, `finished`, `removed`, …).
  On `missed`, replace the state with the fresh snapshot and drop events at or below its `seq`. `seq` restarts
  with each core process, so take a fresh snapshot after reconnecting. A `heartbeat` arrives every 15 s.
- **Compatibility:** call `hello` / `rpc.discover` on connect and check the protocol generation (1 at hc
  0.1.18). The API only grows within a generation.

### 5.2 Local core ↔ machines

- **SSH machines** (e.g. pi): plain `hc machine add <ssh-target> --name pi`. The core retries lost connections
  itself; when SSH needs a password or code again, `hc machine login pi` (noesis key `R`).
- **ET machines** (e.g. the workspace cws, where ET is allowed): `hc machine add --name cws --via '<helper>'`.
  A `--via` command runs locally, gets a shell line as its last argument, must carry stdin/stdout unchanged,
  ask no questions, and **must not request a remote PTY**. ET opens a PTY for its interactive sessions, so the
  likely shape is: a long-lived ET port forward plus, on cws, a bridge that runs `hc connect` per incoming
  connection; the helper connects to the forwarded port. **Unverified** — see open questions.
- **Automatic fallback ET → SSH** (decided 2026-11-08) lives in the **via helper**: try the ET path first,
  otherwise run `ssh cws "<shell line>"`. This is the only noesis code outside the TUI, and it runs on the hub.
- Why ET: it logs in via SSH once, then survives hub sleep and network changes without a new SSH login — this
  addresses the daily re-auth + sleep problem on the workspace.

### 5.3 Trade-offs accepted

- **One hub core holds all connections.** If the hub's core is down, noesis sees nothing — but remote
  terminals keep running (programs live on their machine).
- The ET bridge on cws accepts connections on a local port; **any local user on cws who can reach that port can
  drive its hc core**. Fine on a single-user VM; a risk on a shared host.
- noesis depends on herdr-core's API, which is still **preview** (protocol generation 1, version 0.x).
- The hub can drive agents on every machine, so its SSH/ET credentials are the most sensitive thing in the setup.

### 5.4 Identity

- Terminals have addresses (`t3` locally, `cws/t3` on a machine) and optional names unique among live
  terminals. noesis uses addresses for live operations.
- hc has **no conversation/session id**. noesis needs a stable **thread id** for anything persisted (layout,
  lineage). Proposal: the agent records it as a terminal label (e.g. `thread=<claude session id>`, set by a
  Claude hook via `hc label`), which noesis reads from the `labels` events. Open question.
- Native lineage: every terminal has `parent` (the terminal that started it), and events can be filtered with
  `children_of`. Forks use this (§6.2).

## 6. Threads and knowledge

### 6.1 Purpose (v0.1)

Threads are for **non-code work**: planning, investigation, collecting insights. Their output is knowledge in
the central memory repo, not code. (Code-producing forks with worktrees are out of scope for v0.1.)

### 6.2 Fork (`f`)

- `terminal.run` on the same machine and cwd with `parent` set to the source terminal, starting a forked
  conversation (e.g. `claude --resume <id> --fork-session`) and labels such as `thread-parent=<id>`.
- Forks start with **normal permissions** — no forced plan/read-only mode for now (relaxed 2026-11-08).
- The new thread appears as a child of the source thread (`⑂`).
- hc behaviour to decide on: children **end with their parent** unless started with `outlive_parent`, and the
  parent gets **notes typed into it** when a child needs attention or ends unless `no_notify` (open question).
- Forks may be forked again.

### 6.3 Group context

- Group knowledge is **a view into the central memory**, not a separate store: each group has a context file in
  the memory repo, `groups/<machine>/<group-id>.md`, which points at relevant memories and holds group-specific
  notes.
  **Provisional:** the knowledge repo is organised by projects and topics, not machines, so this path probably
  becomes a per-project context that several host-bound groups point at. How notes from different machines
  merge is being brainstormed in open question 15.
- **Subgroups copy the parent's context file when created** and then evolve independently. Because the file
  holds pointers, shared memories are not duplicated.
- How agents *load* group context at start is open (see open questions).

### 6.4 Roll-up (`u`)

The **child agent writes and pushes its own memory file**; noesis only orchestrates. (Decided 2026-11-08.)

```
hub (noesis)                         machine (child agent)                 GitHub
─────────────                        ─────────────────────                 ──────
1. terminal.send(child, ROLLUP) ──>  2. distill findings
                                     3. write memory/<date>-<slug>.md
                                     4. append index line
                                     5. pull --rebase, commit, push ──────> repo
6. terminal.wait(child) <──────────  (prints ROLLUP-DONE <commit-sha>)
7. verify: sha exists on GitHub
8. terminal.send(parent, "learned X, see <file>")
9. kill child terminal; node -> "✓ <slug> -> knowledge"
```

What noesis owns:

- **The roll-up prompt template** — the only thing keeping memory consistent: filename pattern, frontmatter
  (`name`, `description`, `type`, `group:`, `machine:` tags), index line format, "never edit other memory
  files", "retry push on rejection".
- **A machine-readable finish line:** the child ends with `ROLLUP-DONE <sha>` or `ROLLUP-FAILED <reason>`,
  read via `terminal.read`. (Alternative: the child reports it itself with `hc send` to its parent, which hc
  supports natively — open question.)
- **Verify before closing:** the child terminal ends only after the commit is visible on GitHub. On failure the
  thread stays open and shows `! rollup`.
- **Concurrent writers are expected** (every machine writes). Safety comes from one new file per memory, an
  append-only index (conflicts resolve by keeping both lines), and pull-rebase-retry.
- Nested forks roll up to their **direct parent thread**; knowledge always goes to the memory repo.

## 7. State

| State | Owner | Where |
|---|---|---|
| Terminals, status, labels, parents, transcripts | hc | each machine's core (combined by the hub's core) |
| Groups, order, folds, thread lineage | noesis | hub — local file or an hc document on the hub core (open) |
| Memories, index, group contexts | everyone | GitHub `person-claude-memory` |

Layout stays on the hub (not synced) because there is one hub and layout changes constantly. hc's
**documents** (`doc.get` / `doc.set`: versioned JSON up to 1 MiB, stored atomically in core state, with a
`doc` event on change) are a candidate layout store.

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
| 2026-11-08 | ET primary for the workspace cws (ET allowed there), automatic SSH fallback |
| 2026-11-08 | roll-up: child agent writes + pushes its own memory file |
| 2026-11-08 | build on **herdr-core** (`hc`), not the herdr app; noesis talks only to the local hc core (PR #1 review) |
