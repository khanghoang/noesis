# noesis — open questions

Resume here. Settle **one area at a time**; record the answer in [spec.md](spec.md) (including its decision log)
and delete the question from this file.

## Tree view

1. **Final keymap.** The draft in spec §3.4 hasn't been reviewed. Specifically: is `>`/`<` (indent/outdent) the
   right re-parent gesture, and is `R` free for re-auth?
2. **Status glyphs.** The draft set in spec §3.3 hasn't been reviewed (Nerd Font icons vs plain Unicode).
3. **Where does a new agent start?** `a` on a group needs a cwd, but groups aren't tied to a repo. Proposal:
   a group lists zero or more *roots* (directories), subgroups inherit/copy them, and `a` asks you to pick
   one if there are several.
4. **Strict tree or tags?** Can an agent belong to more than one group? (Current assumption: strict tree.)
5. **What happens to finished threads/agents?** Keep `✓ rolled up` nodes forever, auto-archive after N days,
   or a toggle to hide them?

## Threads and knowledge

6. **How agents load group context at start:** extra directory (`--add-dir`), appended system-prompt file, or a
   CLAUDE.md import. Must work for agents that aren't Claude, or is v0.1 Claude-only?
7. **Group context updates on roll-up.** Proposal: a single y/n at roll-up time, "add this memory to the group
   context?", so group context doesn't grow without limit.
8. **Exact roll-up prompt template** and memory frontmatter (spec §6.4). Should it reuse the existing memory
   format in `person-claude-memory` (`name`, `description`, `metadata.type`) plus `group`/`machine` tags?
9. **Fork command per agent kind.** `claude --resume <id> --fork-session` for Claude; what about other agents
   herdr detects (codex, …)? Is v0.1 Claude-only?

## Topology and transport

10. **Which host is the hub?** Fixed (e.g. always the Mac), or wherever the TUI is opened? A moving hub would
    need the layout store synced after all.
11. **Is the hub's local herdr reached the same way as remote machines** (a "local" transport that's just the
    unix socket)? Assumed yes.
12. **ET details to verify** (ET isn't installed on this VM, so none of this is checked):
    - Can ET forward a unix socket directly, removing the socat bridge and its local-user exposure?
    - How long does `etserver` keep a session while the hub sleeps?
    - Port 2022 reachability from the hub to the workspace cws.
13. **Bridge as a service:** a systemd user unit for socat on cws. Who installs it — manual, or documented in
    dev-env?
14. **First real test (needs herdr running):** run `herdr` on the machine, connect over SSH unix-socket
    forwarding, and confirm `events.subscribe` + `session.snapshot` give everything the tree needs (agent
    status, `agent_session_id`, cwd).

## Implementation

15. **Stack.** Proposal: Rust + ratatui (herdr is probably Rust — unconfirmed; check whether any crate is
    reusable, and what "herdr-core" refers to).
16. **Run inside herdr as a plugin pane** (`plugin.pane.open`) or as a standalone TUI? Check whether a plugin
    pane can host a full interactive TUI.
17. **Layout store format** on the hub (TOML/JSON/SQLite) and how to recover when herdr ids no longer match
    (re-match by `agent_session_id`, then by cwd + agent name?).

## Testing and demos

18. **How to test it end to end.** Proposal, in layers:
    - **Fake herdr:** a small server that speaks herdr's newline-delimited JSON over a unix socket and plays back
      recorded `session.snapshot` responses and event streams (captured from a real herdr 0.9.5). It can also
      inject failures: `events_lost`, a dropped connection, an offline machine. This tests the tree and the
      reconnect logic without real agents.
    - **Transport tests:** run the fake herdr behind real `ssh -L` unix-socket forwarding and behind ET + socat
      on a test host, then kill the link mid-stream and check that noesis reconnects, resubscribes and catches up.
    - **TUI tests:** drive noesis inside tmux (`send-keys` for input, `capture-pane` for output) and compare
      the screen to stored text snapshots. Covers the keymap, folding, reordering, and refused moves across
      machines. If the stack has a test backend (e.g. ratatui's `TestBackend`), use it for fast unit-level
      snapshots too.
    - **Real smoke test:** one scripted run against a real herdr with a cheap agent: fork a thread, roll it up
      into a **scratch** memory repo (never `person-claude-memory`), and check the commit landed.

    Open: which layers are worth it for v0.1, and where tests run (CI on GitHub vs only on cws).
19. **How to capture what it looks like for PRs.** Proposal (user's suggestion): record a scripted session with
    **asciinema**, render it, convert it to **MP4 (H.264)** and attach it to the PR description.
    - Record inside a fixed-size tmux pane (e.g. 120×36) so recordings are reproducible. The same tmux script
      from question 18 can drive the demo, so the video and the test show the same thing.
    - Render the `.cast` with `agg`, passing `--font-dir` with a mono/Nerd font from nixpkgs (e.g.
      jetbrains-mono), otherwise glyphs come out as boxes. Then use `ffmpeg` to make an H.264 MP4 that plays in
      the browser.
    - Attach with `gh` as in the `verify-frontend` skill. Lessons from the AgentTree demos are in the
      `project_agent-tree` memory: keep private session titles out of frame, and use the fake herdr or
      demo-only agents.
    - Keep the `.cast` too (small, text, replayable), e.g. under `docs/demos/` for spec walkthroughs.

    Open: should every UI PR require a recording, and should we also attach a still screenshot (one frame
    rendered from the cast) for quick viewing?

## Later: main view

20. Show the conversation when a node is opened. `agent.read` returns terminal output only; a real conversation
    view likely needs the transcript at `agent_session_path` (e.g. Claude's JSONL) — read over the transport or
    a separate file fetch?
