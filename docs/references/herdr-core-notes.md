# herdr-core facts noesis relies on

Distilled from herdr-core **v0.1.18** (API protocol generation 1, "preview"). ✅ = checked against the saved
docs/schema in [`herdr-core-v0.1.18/`](herdr-core-v0.1.18/); ❓ = assumption still to test. hc isn't installed
on this VM yet, so nothing here has been run.

## What it is

- ✅ herdr-core (`hc`) runs programs and agents in **terminals that stay alive after you leave**. "Core draws
  nothing" — it's meant to be used from a shell, an agent, or your own app. (`README.md`)
- ✅ Separate from the herdr app: its skill says "It is not `herdr`, the older …". Rust, Apache-2.0,
  repo `herdrdev/herdr-core`.

## Data model

- ✅ The unit is a **terminal**: address (`t3`, or `box/t3` on a machine), optional unique `name`, `argv`,
  `cwd`, `state`, `status`, `turn`, `labels`, `parent`, `title`, `foreground` (process + cwd), `keep`, … —
  see `Terminal` in `schema_hc.openrpc.json`.
- ✅ No workspaces, tabs or panes, and **no conversation/session id**.
- ✅ **Parent/child is native:** agents started inside an hc terminal become its children (`parent`, set once).
  Children end with their parent unless `--outlive-parent`; the parent gets notes typed into it when a child
  needs attention or ends, unless `--no-notify`. `hc wait --children all|any` waits on children.
- ✅ **Labels:** `key=value` on terminals (`hc label`, `terminal.label`, `run --label`); `hc ls` / events can
  filter by label.
- ✅ **Documents:** `doc.get` / `doc.set` store opaque JSON per name (≤ 1 MiB), versioned (stale write →
  `conflict`), atomic in core state, survive restart; a `doc` event announces changes (no value, re-read it).
  API-only, works on other machines with `on`. (`schema_README.md`, "Documents")
- ✅ **Templates:** Markdown files with a `command` and role text, started with `hc run <template> "<task>"`.
  They don't install agents or configure status reporting. (`templates.md`)

## Status

- ✅ Status is whatever the program reports through **OSC 7501** (Program Status Protocol): `idle`, `working`,
  `done`, `blocked`, `error`, …. hc never infers it from the screen and doesn't recognise agent brands; a program
  that doesn't report has no status. `turn` goes up each time status leaves `working`.
- ❓ Whether Claude Code (or a hook) emits OSC 7501 — probably needs noesis- or user-provided hooks.

## API and connection

- ✅ Unix socket (named pipe on Windows), **JSON-RPC 2.0, one message per line** ("plain mode").
  `hello {framed: true}` switches to framed mode, needed only for `terminal.attach` streams.
  `hc connect` speaks the same protocol over stdin/stdout, so `ssh box hc connect` is a remote core.
- ✅ Methods: `doc.get/set`, `events.subscribe`, `file.read/write/edit`, `hello`, `machine.add/connect/exec/
  list/rename/rm`, `rpc.discover`, `server.*`, `templates.list`, `terminal.attach/get/interrupt/keep/keys/
  kill/label/list/put/read/rm/run/send/wait`.
- ✅ `terminal.run` params include `on`, `cwd`, `name`, `labels`, `parent`/`no_parent`, `outlive_parent`,
  `no_notify`, `keep`, `rm`, `env`, `wait`.
- ✅ Errors carry a stable `data.kind` and a hint.
- ✅ **Events:** `events.subscribe` replies with a snapshot + `seq`; notifications `event`, `heartbeat`
  (every 15 s), `missed` (fresh snapshot — drop events not above its `seq`). Event types: `created`, `lost`,
  `restarted`, `keep`, `finished`, `removed`, `status`, `turn`, `title`, `labels`, `size`, `foreground`, `doc`.
  `seq` restarts with each core process.
- ✅ Compatibility: the API only grows within a protocol generation; `released.openrpc.json` guards breaks.

## Machines

- ✅ `hc machine add user@host --name box` (SSH) or `--via '<command>'` (custom connection). The remote needs
  hc; add offers to copy it. (`machines.md`)
- ✅ A `--via` command runs locally, gets a shell line as its last argument, must carry stdin/stdout
  unchanged, ask no questions, and must **not** request a remote PTY.
- ✅ **The local core keeps the machine connections and combines terminal lists and events**: terminals on
  added machines appear in the same stream as `rohan/t7`. After a machine reconnects, changed terminals arrive
  as `created` again and vanished ones as `removed`.
- ✅ The core retries lost connections. `hc machine login box` redoes SSH auth; `hc machine update box` copies
  a compatible hc and restarts that core (its terminals keep running). `hc machine rm` doesn't stop remote
  terminals.
- ✅ `hc exec --on box` for short commands, `hc file read/write/edit --on box` for remote files.
- ❓ How an ET-based `--via` helper should be built (see open questions).
