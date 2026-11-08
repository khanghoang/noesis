# cmux-tui ("mux") vs herdr-core

Compared 2026-11-08. cmux's "mux" is **cmux-tui**, the Rust multiplexer in
[manaflow-ai/cmux](https://github.com/manaflow-ai/cmux/tree/a79cbde73ba2ab457253dd2bc1528aa56946f77d/cmux-tui)
(the legacy name survives in `CMUX_MUX_*` env vars, the `mux.json` config file and "mux protocol v12").
cmux-tui facts come from its docs at commit `a79cbde` (`README.md`, `docs/concepts.md`, `docs/machines.md`,
`docs/agent-hooks.md`, `spec/README.md`); herdr-core facts from [herdr-core-notes.md](herdr-core-notes.md)
(v0.1.18). Neither tool has been run on this VM.

Both keep terminals alive with no client attached and are scriptable over a socket. Above that they differ:
cmux-tui is a full tmux/Zellij-style multiplexer with its own UI; hc deliberately draws nothing.

| | **cmux-tui ("mux")** | **herdr-core (`hc`) v0.1.18** |
|---|---|---|
| **What it is** | Daemon + TUI with layouts, sidebar and browser tabs. The engine inside the cmux macOS app, but also runs on its own on Linux and over SSH. | Headless runtime for terminals that stay alive, used from a shell, an agent or your own app. |
| **Data model** | session → workspaces → screens → split panes → tabs. Terminals belong to the session; several tabs can show the same terminal. | Flat list of terminals (`t3`, `box/t3`) with labels. No workspaces, panes or tabs. |
| **Agent hierarchy** | Agents can be grouped by workspace in the sidebar tree; no native parent/child found in the docs. | Native parent/child: children end with their parent, the parent gets notes typed into it, `hc wait --children`. |
| **Agent status** | Agent-aware. `cmux agent hook install claude`, plus an automatic `claude` shim on PATH that merges in its hooks (Codex too). A screen-detection plugin fills in when hooks are silent, e.g. a permission dialog dismissed with Esc. | Agent-agnostic. Only what the program reports via OSC 7501; hc never infers status from the screen. |
| **API** | Two protocols: public `cmux.protocol/2` (125 operations, noun-first `cmux` CLI, 7 SDKs) and private mux v12 for cmux's own frontends. | One protocol: JSON-RPC 2.0 over a Unix socket, OpenRPC schema. Preview (generation 1). |
| **Stored state** | "Frontend projections": opaque personal/shared documents, used only for presentation. Plus a session journal. | `doc.get/set`: versioned JSON documents (≤ 1 MiB) with conflict checking, for any app state. |
| **Multiple machines** | Machine rail switches which session you're attached to, one at a time; the 5 most recent connections stay warm. SSH (strict host keys), cmux.cloud providers, `machine-agent`, WireGuard hub. | The local core joins every added machine into **one terminal list and one event stream** (`machine add` over SSH or `--via`). |
| **Extras** | Browser tabs over Chrome DevTools, kitty graphics, scrollable columns, layout undo. | Templates, `hc exec --on`, remote file read/write/edit. |
| **License** | AGPL; very actively developed. | Apache-2.0. |

## What it means for noesis

- **hc fits the design better.** The merged stream across machines plus native parent/child is what the
  `@host group` tree is built on; cmux-tui shows one machine at a time.
- **cmux-tui is ahead on agent status.** Its Claude shim and screen detection give status without setup. With
  hc, noesis or the user still has to make Claude Code emit OSC 7501 (still ❓ in
  [herdr-core-notes.md](herdr-core-notes.md#status)). The shim approach (wrap `claude` on PATH, merge every
  `--settings` into one file with the hooks added) is worth borrowing.
- **cmux-tui overlaps with noesis itself.** Its sidebar already draws collapsible machine/workspace/agent trees,
  so building on it would mean fitting into its UI instead of owning the tree view.
