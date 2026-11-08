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
   or a toggle to hide them? (hc can hide finished terminals; `terminal.list` reports `hidden_finished`.)

## herdr-core integration

6. **Making agents report status.** hc only knows status that the program reports via OSC 7501, and templates
   don't configure that. Claude Code needs something (e.g. hooks that emit OSC 7501 on start, stop, and
   permission prompts) or noesis shows `·` for every agent. Is this a noesis-provided hook set, or does
   herdr-core ship one?
7. **Thread id.** hc has no conversation id. Proposal: a Claude hook runs `hc label <terminal>
   thread=<session id>` so noesis can persist by thread. Alternatives: noesis starts Claude with a known
   `--session-id`; or reads it from the transcript path.
8. **Where groups live.** Options: only in noesis's layout; also mirrored as terminal labels (`group=<id>`) so
   other hc clients and `hc ls --label` see them; or each machine's group tree in an hc document on that
   machine.
9. **Fork and hc parent/child behaviour.** Should forks use `outlive_parent` (so closing the parent doesn't
   end the fork) and `no_notify` (so hc doesn't type notes into the parent)? Or are those notes exactly the
   roll-up channel we want?
10. **Use hc templates for agent roles?** e.g. a `rollup` or `investigate` template with the roll-up rules in
    its role text, instead of noesis sending a long prompt.

## Threads and knowledge

11. **How agents load group context at start:** extra directory (`--add-dir`), appended system-prompt file, or a
    CLAUDE.md import. Must work for agents that aren't Claude, or is v0.1 Claude-only?
12. **Group context updates on roll-up.** Proposal: a single y/n at roll-up time, "add this memory to the group
    context?", so group context doesn't grow without limit.
13. **Exact roll-up prompt template** and memory frontmatter (spec §6.4). Should it reuse the existing memory
    format in `person-claude-memory` (`name`, `description`, `metadata.type`) plus `group`/`machine` tags? And
    does the child report `ROLLUP-DONE` on screen or via `hc send` to its parent?
14. **Fork command per agent kind.** `claude --resume <id> --fork-session` for Claude; what about other agents
    (codex, pi, …)? Is v0.1 Claude-only?

## Topology and connections

15. **Which host is the hub?** Fixed (e.g. always the Mac), or wherever the TUI is opened? A moving hub would
    need the layout store synced after all.
16. **ET via helper — verify the mechanism** (ET isn't installed on this VM, nothing is checked):
    - Can an ET command carry a plain byte stream without a PTY, or is a port forward + bridge required?
    - Bridge on cws: e.g. `socat TCP-LISTEN:<port>,bind=127.0.0.1,fork EXEC:'hc connect'` as a systemd user
      unit. Who installs it — manual, or dev-env?
    - How long does `etserver` keep a session while the hub sleeps? Is port 2022 reachable from the hub?
    - Does the helper's ET → SSH fallback behave well with hc's own reconnect retries?
17. **First real test:** install `hc` on cws and the hub, `hc machine add` over SSH, then confirm one
    `events.subscribe` on the hub's core shows both machines with status, labels and parents.

## Implementation

18. **Stack.** herdr-core is Rust. Proposal: Rust + ratatui, possibly reusing herdr-core's crates for the API
    types (check whether they're published or usable as a git dependency) — otherwise generate types from
    `hc.openrpc.json`.
19. **Layout store:** a local file (TOML/JSON/SQLite) vs an hc document on the hub core (`doc.set`, versioned,
    atomic). And how to recover when terminal addresses no longer match (re-match by thread label?).

## Testing and demos

20. **How to test it end to end.** Proposal, in layers:
    - **Fake core:** a small server that speaks hc's JSON-RPC over a unix socket and plays back recorded
      `events.subscribe` snapshots and event streams (captured from a real hc 0.1.18). It can also inject
      failures: `missed`, a dropped connection, an offline machine. This tests the tree and the reconnect
      logic without real agents.
    - **Connection tests:** a real hc core with a second machine added over SSH and over the ET via helper,
      then kill the link mid-stream and check that noesis catches up after the core reconnects.
    - **TUI tests:** drive noesis inside tmux (`send-keys` for input, `capture-pane` for output) and compare
      the screen to stored text snapshots. Covers the keymap, folding, reordering, and refused moves across
      machines. If the stack has a test backend (e.g. ratatui's `TestBackend`), use it for fast unit-level
      snapshots too.
    - **Real smoke test:** one scripted run against a real hc with a cheap agent: fork a thread, roll it up into
      a **scratch** memory repo (never `person-claude-memory`), and check the commit landed.

    Open: which layers are worth it for v0.1, and where tests run (CI on GitHub vs only on cws).
21. **How to capture what it looks like for PRs.** Proposal (user's suggestion): record a scripted session with
    **asciinema**, render it, convert it to **MP4 (H.264)** and attach it to the PR description.
    - Record inside a fixed-size tmux pane (e.g. 120×36) so recordings are reproducible. The same tmux script
      from question 20 can drive the demo, so the video and the test show the same thing.
    - Render the `.cast` with `agg`, passing `--font-dir` with a mono/Nerd font from nixpkgs (e.g.
      jetbrains-mono), otherwise glyphs come out as boxes. Then use `ffmpeg` to make an H.264 MP4 that plays in
      the browser.
    - Attach with `gh` as in the `verify-frontend` skill. Lessons from the AgentTree demos are in the
      `project_agent-tree` memory: keep private session titles out of frame, and use the fake core or
      demo-only agents.
    - A first version exists for the spec: [`assets/make-demo.sh`](../assets/make-demo.sh) records the scripted
      mock in [`assets/`](../assets/) and renders `assets/noesis-mock-demo.mp4`. The same pipeline can record
      the real TUI later.

    Open: should every UI PR require a recording, and should we also attach a still screenshot (one frame
    rendered from the cast) for quick viewing?

## Later: main view

22. Show the conversation when a node is opened. `terminal.attach` (framed mode) streams the live screen;
    a real conversation view likely needs the transcript (e.g. Claude's JSONL) — read with `file.read` over the
    core, which works on any machine?
