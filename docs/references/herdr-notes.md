# herdr facts noesis relies on

Distilled from herdr 0.9.5 (protocol 22). ✅ = checked against the saved docs/schema or the installed CLI;
❓ = assumption still to test. File references are to [`herdr-v0.9.5/`](herdr-v0.9.5/).

## Data model

- ✅ herdr hierarchy: **machine → session → workspace → tab → pane → agent**. No groups, no agent ordering,
  no parent/child links between agents — noesis must own all of that.
- ✅ Workspaces can be reordered natively (`workspace.move`, `workspace.move_block`), but noesis doesn't map
  groups to workspaces (groups nest and aren't tied to cwd).
- ✅ Workspace metadata (`workspace.report_metadata`) is limited to 16 tokens, 32-char keys, TTL ≤ 24h —
  **not usable for durable state**.
- ✅ Agent conversations: `pane.report_agent_session` carries `agent_session_id`, `agent_session_path` and
  `resume_argv` (command that resumes the session after a herdr restart). Responses expose `AgentSessionInfo`.
- ✅ Ids (`w1:p1`, agent names) are scoped to one server; two machines can both have `w1:p1`.
- ❓ Pane ids change across herdr restarts — which is why noesis persists by `agent_session_id`.

## Socket API

- ✅ Newline-delimited JSON over a unix socket (`~/.config/herdr/herdr.sock` by default). One request per
  line: `{"id":"req_1","method":"ping","params":{}}` → `{"id":"req_1","result":{...}}`.
  (`socket-api.mdx`, "Socket transport")
- ✅ Useful methods: `session.snapshot`, `events.subscribe`, `agent.list/get/read/prompt/wait/start/focus`,
  `pane.close/read/split`, `workspace.*`, `worktree.*`, `plugin.pane.open`. Full list in `api-schema.json`.
- ✅ `agent.prompt` takes an optional `wait` (`until`, `timeout_ms`) so prompting and waiting happen in one
  request, with no race. It returns `agent_blocked` if the agent is already blocked.
- ✅ `events.subscribe` keeps the connection open: first line acknowledges, later lines are events. Pane
  events include `pane.created/updated/closed/exited`, `pane.agent_detected`, `pane.agent_status_changed`.
  If any referenced pane doesn't exist, the whole request is rejected and the connection closed.
- ✅ **Recovery:** events aren't durable. On `events_lost` (or reconnect): open a new subscription, wait for
  `subscription_started`, then call `session.snapshot` on **another connection**. Replace the cache with the
  snapshot; treat events as invalidation signals that trigger reads; never replay buffered events onto a
  snapshot. → Transports must allow several concurrent connections.
- ✅ Compatibility: JSON API clients should ignore unknown fields and treat unsupported methods as normal
  errors. (`socket-api.mdx`, "Protocol stability")

## Machines (`herdr machine`, `--machine`)

- ✅ `herdr machine add <ssh-target>` runs **on the client (hub)**. It SSHes in, offers to install/update herdr
  (with approval, interactive terminal), starts the remote server, and saves a profile (id, label, SSH target,
  remote session, enabled). No credentials are stored. One profile = one remote session.
- ✅ Reconnects automatically with backoff up to 2 minutes; background reconnects never install or restart.
- ✅ `herdr --machine <label> <cmd>` forwards the JSON API over **non-interactive SSH**, one machine at a time,
  no combined listings. Forwarded: `workspace`, `worktree`, `tab`, `pane`, `notification`, `agent` (not
  `attach`), `api snapshot`, `status server`, plugin commands. **`events.subscribe` isn't listed** → no live
  event stream via `--machine`. (`cli-reference.mdx`, "Saved SSH machines")
- ✅ SSH-only (OpenSSH, shared ControlMaster with `ControlPersist 600`). No ET support.
- ✅ The socket API itself has no machine fields; machines exist only at the CLI/UI level.

## Other

- ✅ `plugin.pane.open` exists — noesis *could* live inside herdr as a pane. ❓ whether a plugin pane can host
  a full interactive TUI.
- ❓ herdr is written in Rust; ❓ what "herdr-core" refers to (a crate?).
